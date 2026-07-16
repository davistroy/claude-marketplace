"""Regression tests: XXE (XML External Entity) hardening for the BPMN parser.

The parser must never resolve external entities defined via a DOCTYPE
declaration. These tests attempt to exfiltrate the contents of a local file
(a temp file with a unique sentinel — portable across POSIX and Windows,
unlike a hardcoded /etc/hostname) through both a text node and an attribute
value; in both cases the sentinel content must never surface in the parsed
model, either because the entity is left unresolved or because the parser
rejects the document.
"""

from pathlib import Path

from bpmn2drawio.exceptions import BPMNParseError
from bpmn2drawio.parser import parse_bpmn

SENTINEL = "XXE_LEAK_SENTINEL_9f3a2b7c"


def _xml_with_entity(system_uri: str, *, in_attribute: bool) -> str:
    """Build a BPMN document whose DOCTYPE defines an external SYSTEM entity
    pointing at ``system_uri``, referenced either in a text node or an
    attribute value.
    """
    entity_ref = "&xxe;"
    if in_attribute:
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE bpmn:definitions [ <!ENTITY xxe SYSTEM "{system_uri}"> ]>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  id="Definitions_1" targetNamespace="http://example.org/bpmn">
  <bpmn:process id="Process_1" name="{entity_ref}" isExecutable="true">
    <bpmn:startEvent id="Start_1"/>
    <bpmn:endEvent id="End_1"/>
  </bpmn:process>
</bpmn:definitions>
"""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE bpmn:definitions [ <!ENTITY xxe SYSTEM "{system_uri}"> ]>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  id="Definitions_1" targetNamespace="http://example.org/bpmn">
  <bpmn:process id="Process_1" name="Test" isExecutable="true">
    <bpmn:startEvent id="Start_1"/>
    <bpmn:task id="Task_1"/>
    <bpmn:endEvent id="End_1"/>
    <bpmn:sequenceFlow id="Flow_1" sourceRef="Start_1" targetRef="Task_1">
      <bpmn:conditionExpression>{entity_ref}</bpmn:conditionExpression>
    </bpmn:sequenceFlow>
    <bpmn:sequenceFlow id="Flow_2" sourceRef="Task_1" targetRef="End_1"/>
  </bpmn:process>
</bpmn:definitions>
"""


class TestXXEHardening:
    """The parser must not resolve external entities from untrusted BPMN XML."""

    def _secret_uri(self, tmp_path: Path) -> str:
        secret = tmp_path / "secret.txt"
        secret.write_text(SENTINEL, encoding="utf-8")
        # Path.as_uri() yields a valid file:// URI on both POSIX and Windows.
        return secret.as_uri()

    def test_entity_in_text_node_is_not_resolved(self, tmp_path):
        """An entity referencing a local file inside a text node must not leak
        its content into the parsed model — either the value stays absent/None
        or a BPMNParseError is raised. Never the actual file content.
        """
        xml = _xml_with_entity(self._secret_uri(tmp_path), in_attribute=False)
        try:
            model = parse_bpmn(xml)
        except BPMNParseError:
            # Rejecting the document outright is an acceptable safe outcome.
            return

        flow = model.get_flow_by_id("Flow_1")
        assert flow is not None
        assert flow.condition is None or SENTINEL not in flow.condition

    def test_entity_in_attribute_is_not_resolved(self, tmp_path):
        """An entity referencing a local file inside an attribute value must
        never surface as the resolved file content. lxml disallows external
        entity references in attribute values once resolve_entities=False, so
        this is expected to raise BPMNParseError — but even if a future lxml
        version changes that behavior, the sentinel content must not appear.
        """
        xml = _xml_with_entity(self._secret_uri(tmp_path), in_attribute=True)
        try:
            model = parse_bpmn(xml)
        except BPMNParseError:
            # Safe: parser rejected the malicious document.
            return

        assert model.process_name is None or SENTINEL not in model.process_name

    def test_fromstring_entry_point_does_not_resolve_entities(self, tmp_path):
        """Exercise the string-input branch of BPMNParser.parse() (etree.fromstring)
        directly, independent of file-path parsing (etree.parse).
        """
        xml = _xml_with_entity(self._secret_uri(tmp_path), in_attribute=False)
        try:
            model = parse_bpmn(xml.strip())
        except BPMNParseError:
            return

        flow = model.get_flow_by_id("Flow_1")
        assert flow is not None
        assert flow.condition is None or SENTINEL not in (flow.condition or "")
