"""Regression tests: XXE (XML External Entity) hardening for the BPMN parser.

The parser must never resolve external entities defined via a DOCTYPE
declaration. These tests attempt to exfiltrate the contents of /etc/hostname
through both a text node and an attribute value; in both cases the real
file content must never surface in the parsed model, either because the
entity is left unresolved or because the parser rejects the document.
"""

from pathlib import Path

import pytest

from bpmn2drawio.exceptions import BPMNParseError
from bpmn2drawio.parser import parse_bpmn

HOSTNAME_CONTENT = Path("/etc/hostname").read_text().strip()

# Entity reference inside a text node (bpmn:conditionExpression body).
XXE_TEXT_NODE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE bpmn:definitions [ <!ENTITY xxe SYSTEM "file:///etc/hostname"> ]>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  id="Definitions_1" targetNamespace="http://example.org/bpmn">
  <bpmn:process id="Process_1" name="Test" isExecutable="true">
    <bpmn:startEvent id="Start_1"/>
    <bpmn:task id="Task_1"/>
    <bpmn:endEvent id="End_1"/>
    <bpmn:sequenceFlow id="Flow_1" sourceRef="Start_1" targetRef="Task_1">
      <bpmn:conditionExpression>&xxe;</bpmn:conditionExpression>
    </bpmn:sequenceFlow>
    <bpmn:sequenceFlow id="Flow_2" sourceRef="Task_1" targetRef="End_1"/>
  </bpmn:process>
</bpmn:definitions>
"""

# Entity reference inside an attribute value (process name).
XXE_ATTRIBUTE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE bpmn:definitions [ <!ENTITY xxe SYSTEM "file:///etc/hostname"> ]>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  id="Definitions_1" targetNamespace="http://example.org/bpmn">
  <bpmn:process id="Process_1" name="&xxe;" isExecutable="true">
    <bpmn:startEvent id="Start_1"/>
    <bpmn:endEvent id="End_1"/>
  </bpmn:process>
</bpmn:definitions>
"""


class TestXXEHardening:
    """The parser must not resolve external entities from untrusted BPMN XML."""

    def test_entity_in_text_node_is_not_resolved(self):
        """An entity referencing /etc/hostname inside a text node must not leak
        its content into the parsed model — either the value stays absent/None
        or a BPMNParseError is raised. Never the actual file content.
        """
        try:
            model = parse_bpmn(XXE_TEXT_NODE_XML)
        except BPMNParseError:
            # Rejecting the document outright is an acceptable safe outcome.
            return

        flow = model.get_flow_by_id("Flow_1")
        assert flow is not None
        assert flow.condition != HOSTNAME_CONTENT
        assert flow.condition is None or HOSTNAME_CONTENT not in flow.condition

    def test_entity_in_attribute_is_not_resolved(self):
        """An entity referencing /etc/hostname inside an attribute value must
        never surface as the resolved file content. lxml disallows external
        entity references in attribute values once resolve_entities=False, so
        this is expected to raise BPMNParseError — but even if a future lxml
        version changes that behavior, the hostname content must not appear.
        """
        try:
            model = parse_bpmn(XXE_ATTRIBUTE_XML)
        except BPMNParseError:
            # Safe: parser rejected the malicious document.
            return

        assert model.process_name != HOSTNAME_CONTENT
        assert model.process_name is None or HOSTNAME_CONTENT not in model.process_name

    def test_fromstring_entry_point_does_not_resolve_entities(self):
        """Exercise the string-input branch of BPMNParser.parse() (etree.fromstring)
        directly, independent of file-path parsing (etree.parse).
        """
        try:
            model = parse_bpmn(XXE_TEXT_NODE_XML.strip())
        except BPMNParseError:
            return

        flow = model.get_flow_by_id("Flow_1")
        assert flow is not None
        assert flow.condition is None or HOSTNAME_CONTENT not in (flow.condition or "")
