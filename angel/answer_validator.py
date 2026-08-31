import re

class AnswerValidator:
    """Application-side source claim checks. The retrieval manifest is authoritative."""
    def source_violations(self,answer,manifest):
        allowed=set(manifest.filenames()) if manifest else set()
        found=set(re.findall(r"(?<![\w-])([A-Za-z0-9_.-]+\.md)(?![\w-])",answer or ""))
        return sorted(found-allowed)

    def source_metadata_violations(self,answer,manifest):
        if not manifest:return []
        out=[]
        for s in manifest.sources:
            pat=re.compile(rf"(?i){re.escape(s.filename)}.*?(?:from|in|belongs to|part of|collection)\s+(?:the\s+)?([A-Za-z0-9_-]+)")
            for m in pat.finditer(answer or ""):
                claimed=m.group(1).lower()
                if claimed not in {s.domain.lower(),s.topic.lower()}:
                    out.append({"filename":s.filename,"claimed":claimed,"actual_domain":s.domain,"actual_topic":s.topic})
        return out
