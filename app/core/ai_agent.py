# app/core/ai_agent.py
from typing import List, Union, Tuple
import logging
import re
from urllib.parse import urlparse

from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain.output_parsers import StructuredOutputParser, ResponseSchema, OutputFixingParser

# Optional: HTML→Text for tool outputs (safe if available)
try:
    from langchain_community.document_transformers import Html2TextTransformer
    from langchain_core.documents import Document
    _HAS_HTML_TX = True
except Exception:
    _HAS_HTML_TX = False

# ---------- Patterns & small utils ----------

_URL_RE = re.compile(r"https?://[^\s\]\)\}<>\"']+")
_MULTIBLANK_RE = re.compile(r"\n{3,}")
_BR_RE = re.compile(r"<\s*br\s*/?\s*>", flags=re.IGNORECASE)

# Detect inline tool-call markup inside AIMessage.content
_TOOLCALL_INLINE_RE = re.compile(
    r"""<
        \s*(?:function|tool|tavily[_-]?\w*|search)\s*  # <function=..., <tool ..., <tavily_search ...
        [^>]*>
        \s*\{.*\}
    """,
    re.IGNORECASE | re.VERBOSE | re.DOTALL,
)

def _normalize_text(s: str) -> str:
    """Light normalization: drop <br>, normalize newlines, limit blank lines, trim."""
    if not s:
        return ""
    s = _BR_RE.sub("\n", s)
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = _MULTIBLANK_RE.sub("\n\n", s)
    return "\n".join(line.rstrip() for line in s.split("\n")).strip()

def _extract_urls(text: str) -> List[str]:
    return _URL_RE.findall(text or "")

def _summarize_sources(urls: List[str], limit: int = 5) -> List[Tuple[str, str]]:
    """Return up to `limit` unique sources as (domain, url)."""
    seen = set()
    picked: List[Tuple[str, str]] = []
    for url in urls:
        try:
            dom = urlparse(url).netloc.lower()
            if dom.startswith("www."):
                dom = dom[4:]
            key = (dom, url)
            if dom and key not in seen:
                seen.add(key)
                picked.append((dom, url))
                if len(picked) >= limit:
                    break
        except Exception:
            continue
    return picked

def _is_tool_message(m) -> bool:
    """Works across versions (ToolMessage class or dict-shaped)."""
    try:
        if getattr(m, "__class__", None) and m.__class__.__name__ == "ToolMessage":
            return True
        if isinstance(m, dict) and m.get("type") == "tool":
            return True
    except Exception:
        pass
    return False

def _get_message_content(m) -> str:
    if isinstance(m, (AIMessage, HumanMessage, SystemMessage)):
        return m.content or ""
    if isinstance(m, dict):
        return str(m.get("content", "") or "")
    return str(getattr(m, "content", "") or "")

def _looks_like_toolcall_text(s: str) -> bool:
    """Heuristic: AI message content contains inline tool-call markup."""
    if not s:
        return False
    return bool(_TOOLCALL_INLINE_RE.search(s))


# ---------- Tools ----------

def _make_tools(allow_search: bool):
    """Create optional tools; keep outputs concise to aid synthesis."""
    if not allow_search:
        return []
    try:
        return [TavilySearch(
            max_results=3,
            search_depth="advanced",
            include_answer=True,       # concise summaries
            include_raw_content=False  # avoid large dumps
        )]
    except Exception as e:
        logging.exception("Failed to init Tavily tool: %s", e)
        return []


# ---------- Main entrypoint ----------

def get_response_from_ai_agents(
    llm_id: str,
    messages: List[str],        # list of user strings
    allow_search: bool,
    system_prompt: str,
) -> str:
    """
    Run ReAct; if tools were used or the final message looks like a tool-call,
    do a grounded structured synthesis to guarantee a clean NL answer.
    """
    # LLM (requires GROQ_API_KEY). Lower temperature to reduce drift.
    llm = ChatGroq(model=llm_id, temperature=0.2)

    # Optional Tavily tool (requires TAVILY_API_KEY)
    tools = _make_tools(allow_search)

    # Create agent (newer langgraph uses prompt= ; older used state_modifier=)
    try:
        agent = create_react_agent(model=llm, tools=tools, prompt=system_prompt)
    except TypeError:
        agent = create_react_agent(model=llm, tools=tools, state_modifier=system_prompt)

    # Build conversation: System + each user message as Human
    convo = [SystemMessage(content=system_prompt)] if system_prompt else []
    for msg in messages:
        convo.append(HumanMessage(content=msg))

    state = {"messages": convo}

    # Let the graph run internal steps (tools → reasoning → answer)
    state = agent.invoke(state, config={"recursion_limit": 80})
    out_messages: List[Union[AIMessage, HumanMessage, SystemMessage, dict]] = state.get("messages", [])

    # --- Gather tool outputs (raw) ---
    used_tools = False
    raw_chunks: List[str] = []
    for m in out_messages:
        if _is_tool_message(m):
            used_tools = True
            raw_chunks.append(_get_message_content(m))

    # --- Determine final AI text (skip tool-call-like content) ---
    final_ai_text = ""
    final_ai_looks_like_toolcall = False

    for m in reversed(out_messages):
        if isinstance(m, AIMessage) and not getattr(m, "tool_calls", None):
            candidate = _normalize_text(m.content or "")
            if candidate and not _looks_like_toolcall_text(candidate):
                final_ai_text = candidate
                break
            else:
                # it exists, but looks like an inline tool-call; mark it
                final_ai_looks_like_toolcall = True
                # don't break; continue searching earlier AI messages

    # If no tools used AND we have a clean final AI text, just return it
    if not used_tools and final_ai_text:
        return final_ai_text

    # Clean tool text (HTML → text) using transformer if available
    if _HAS_HTML_TX and raw_chunks:
        try:
            tx = Html2TextTransformer()
            docs = [Document(page_content=_normalize_text(t)) for t in raw_chunks]
            cleaned_docs = tx.transform_documents(docs)
            tool_chunks = [d.page_content for d in cleaned_docs]
        except Exception:
            tool_chunks = [_normalize_text(t) for t in raw_chunks]
    else:
        tool_chunks = [_normalize_text(t) for t in raw_chunks]

    # Extract and whitelist sources from tool text
    all_urls: List[str] = []
    for t in tool_chunks:
        all_urls.extend(_extract_urls(t))
    picked_sources = _summarize_sources(all_urls, limit=5)
    sources_str = "\n".join(f"- {dom} — {url}" for dom, url in picked_sources) if picked_sources else "(no URLs captured)"

    # ---------- Structured synthesis (JSON) ----------
    schemas = [
        ResponseSchema(name="answer", description="Final answer in Markdown, no HTML."),
        ResponseSchema(name="bullets", description="Key points as a list of short strings."),
        ResponseSchema(name="references", description="List of strings; each string is 'domain — url' only from Allowed sources."),
    ]
    parser = StructuredOutputParser.from_response_schemas(schemas)
    fmt_instructions = parser.get_format_instructions()
    fixing_parser = OutputFixingParser.from_llm(parser=parser, llm=llm)

    # Instructions (two paths):
    # - If we have tool findings: ground the synthesis in those findings & allowed sources
    # - If we *don't* have tool findings (e.g., tool-call emitted but tool failed), answer with model knowledge and say search wasn't used
    if tool_chunks:
        synthesis_instructions = (
            "Return JSON ONLY in the exact format specified (no surrounding prose). "
            "Your JSON must have keys: answer, bullets, references. "
            "The 'answer' must be in Markdown, no HTML. "
            "Ground the answer strictly in the provided 'Search findings'. "
            "Cite ONLY from 'Allowed sources'; if you cite, each entry must be 'domain — url' from that list. "
            "If the findings are insufficient, say so in 'answer'."
        )

        user_question = messages[-1] if messages else ""
        findings_text = "\n\n".join([c for c in tool_chunks if c])[:8000]

        synthesis_prompt = [
            SystemMessage(content=synthesis_instructions + "\n\n" + fmt_instructions),
            HumanMessage(content=f"User question:\n{user_question}"),
            HumanMessage(content=f"Allowed sources (use ONLY these if you cite):\n{sources_str}"),
            HumanMessage(content=f"Search findings (clean excerpts):\n{findings_text or '(no findings captured)'}"),
            HumanMessage(content=f"Agent draft (if any):\n{final_ai_text or '(none)'}"),
        ]
    else:
        # No tool findings captured: provide a clean LLM-only answer and be transparent.
        synthesis_instructions = (
            "Return JSON ONLY in the exact format specified (no surrounding prose). "
            "Your JSON must have keys: answer, bullets, references. "
            "The 'answer' must be in Markdown, no HTML. "
            "The web-search findings were not available; answer based on general knowledge. "
            "Do NOT fabricate citations; leave 'references' empty."
        )

        user_question = messages[-1] if messages else ""
        synthesis_prompt = [
            SystemMessage(content=synthesis_instructions + "\n\n" + fmt_instructions),
            HumanMessage(content=f"User question:\n{user_question}"),
            HumanMessage(content=f"Context:\nNo verified search findings were available due to missing tool results."),
            HumanMessage(content=f"Agent draft (if any):\n{final_ai_text or '(none)'}"),
        ]

    try:
        raw = llm.invoke(synthesis_prompt)
        content = getattr(raw, "content", "") if raw else ""
        data = fixing_parser.parse(content)  # structured dict
        # Compose final Markdown deterministically
        out = _normalize_text(data.get("answer", ""))

        bullets = data.get("bullets") or []
        if isinstance(bullets, list) and bullets:
            out += "\n\n**Key points**\n" + "\n".join(f"- {str(b).strip()}" for b in bullets if str(b).strip())

        refs = data.get("references") or []
        if isinstance(refs, list) and refs:
            out += "\n\n**References**\n" + "\n".join(f"- {str(r).strip()}" for r in refs if str(r).strip())

        return out.strip() or final_ai_text
    except Exception as e:
        logging.exception("Structured synthesis failed: %s", e)
        # Fallbacks:
        if final_ai_text and not _looks_like_toolcall_text(final_ai_text):
            return final_ai_text
        # Last-resort: minimal helpful answer
        return "I couldn’t complete the web-search step just now, so I answered from general knowledge."