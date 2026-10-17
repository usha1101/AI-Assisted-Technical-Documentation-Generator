from typing import List, Dict, Any, Optional
from app.models import DocstringStyle


class DocstringFormatter:
    """
    Formats raw AI explanations into standard industry docstring conventions:
    Google Style, Sphinx / reST Style, NumPy Style, or Concise / Detailed summary.
    """

    @staticmethod
    def format_docstring(
        summary: str,
        parameters: Optional[List[Dict[str, Any]]] = None,
        return_type: Optional[str] = None,
        raises: Optional[List[str]] = None,
        style: DocstringStyle = DocstringStyle.CONCISE,
        indent: str = "    "
    ) -> str:
        """
        Builds a structured docstring string without surrounding quotes.
        """
        summary_text = (summary or "").strip()
        params = [p for p in (parameters or []) if p.get('name') not in ('self', 'cls')]
        exceptions = raises or []

        # Return plain summary if concise or detailed or if there is no metadata
        if style in (DocstringStyle.CONCISE, DocstringStyle.DETAILED):
            return summary_text

        if style == DocstringStyle.GOOGLE:
            return DocstringFormatter._format_google(summary_text, params, return_type, exceptions)
        elif style == DocstringStyle.SPHINX:
            return DocstringFormatter._format_sphinx(summary_text, params, return_type, exceptions)
        elif style == DocstringStyle.NUMPY:
            return DocstringFormatter._format_numpy(summary_text, params, return_type, exceptions)
        else:
            return summary_text

    @staticmethod
    def _format_google(
        summary: str,
        params: List[Dict[str, Any]],
        return_type: Optional[str],
        raises: List[str]
    ) -> str:
        lines = [summary] if summary else []

        if params:
            if lines:
                lines.append("")
            lines.append("Args:")
            for p in params:
                name = p.get('name', '')
                t = p.get('type_annotation')
                d = p.get('default_value')

                type_part = f" ({t})" if t else ""
                default_part = f". Defaults to {d}." if d is not None else ""
                lines.append(f"    {name}{type_part}: The {name} argument{default_part}")

        if return_type and return_type.lower() != 'none':
            if lines:
                lines.append("")
            lines.append("Returns:")
            lines.append(f"    {return_type}: The computed result.")

        if raises:
            if lines:
                lines.append("")
            lines.append("Raises:")
            for r in raises:
                lines.append(f"    {r}: If an error occurs during processing.")

        return "\n".join(lines)

    @staticmethod
    def _format_sphinx(
        summary: str,
        params: List[Dict[str, Any]],
        return_type: Optional[str],
        raises: List[str]
    ) -> str:
        lines = [summary] if summary else []

        if params:
            if lines:
                lines.append("")
            for p in params:
                name = p.get('name', '')
                t = p.get('type_annotation')
                d = p.get('default_value')
                default_part = f" Defaults to {d}." if d is not None else ""
                lines.append(f":param {name}: The {name} argument.{default_part}")
                if t:
                    lines.append(f":type {name}: {t}")

        if return_type and return_type.lower() != 'none':
            if lines:
                lines.append("")
            lines.append(":return: The computed result.")
            lines.append(f":rtype: {return_type}")

        if raises:
            if lines:
                lines.append("")
            for r in raises:
                lines.append(f":raises {r}: If an error occurs during processing.")

        return "\n".join(lines)

    @staticmethod
    def _format_numpy(
        summary: str,
        params: List[Dict[str, Any]],
        return_type: Optional[str],
        raises: List[str]
    ) -> str:
        lines = [summary] if summary else []

        if params:
            if lines:
                lines.append("")
            lines.append("Parameters")
            lines.append("----------")
            for p in params:
                name = p.get('name', '')
                t = p.get('type_annotation')
                d = p.get('default_value')
                type_spec = f" : {t}" if t else ""
                if d is not None:
                    type_spec += f", optional"
                lines.append(f"{name}{type_spec}")
                desc = f"    The {name} parameter."
                if d is not None:
                    desc += f" Default is {d}."
                lines.append(desc)

        if return_type and return_type.lower() != 'none':
            if lines:
                lines.append("")
            lines.append("Returns")
            lines.append("-------")
            lines.append(return_type)
            lines.append("    The computed result.")

        if raises:
            if lines:
                lines.append("")
            lines.append("Raises")
            lines.append("------")
            for r in raises:
                lines.append(r)
                lines.append("    If an error occurs during processing.")

        return "\n".join(lines)
