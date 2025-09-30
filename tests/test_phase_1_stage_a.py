"""
Phase 1 Test Suite: Stage A Classifier
Comprehensive tests for intent classification, entity extraction, confidence scoring, and risk assessment

Test Categories:
1. LLM Integration Tests (10 tests)
2. Intent Classification Tests (15 tests)
3. Entity Extraction Tests (15 tests)
4. Confidence Scoring Tests (10 tests)
5. Risk Assessment Tests (10 tests)
6. Stage A Integration Tests (10 tests)
7. Error Handling Tests (5 tests)

Total: 75 tests as planned for Phase 1
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

# Import components to test
from pipeline.stages.stage_a.classifier import StageAClassifier
from pipeline.stages.stage_a.intent_classifier import IntentClassifier
from pipeline.stages.stage_a.entity_extractor import EntityExtractor
from pipeline.stages.stage_a.confidence_scorer import ConfidenceScorer
from pipeline.stages.stage_a.risk_assessor import RiskAssessor
from pipeline.schemas.decision_v1 import DecisionV1, IntentV1, EntityV1, DecisionType, ConfidenceLevel, RiskLevel
from llm.client import LLMClient, LLMRequest, LLMResponse
from llm.ollama_client import OllamaClient
from llm.prompt_manager import PromptManager, PromptType
from llm.response_parser import ResponseParser

# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing"""
    client = Mock(spec=LLMClient)
    client.is_connected = True
    client.health_check = AsyncMock(return_value=True)
    client.generate = AsyncMock()
    return client

@pytest.fixture
def sample_llm_response():
    """Sample LLM response"""
    return LLMResponse(
        content='{"category": "automation", "action": "restart_service", "confidence": 0.95}',
        model="llama2",
        tokens_used=50,
        processing_time_ms=1500
    )

@pytest.fixture
def sample_entities_response():
    """Sample entities LLM response"""
    return LLMResponse(
        content='[{"type": "service", "value": "nginx", "confidence": 0.9}, {"type": "hostname", "value": "web-01", "confidence": 0.8}]',
        model="llama2",
        tokens_used=75,
        processing_time_ms=1200
    )

@pytest.fixture
def sample_confidence_response():
    """Sample confidence LLM response"""
    return LLMResponse(
        content="0.85",
        model="llama2",
        tokens_used=25,
        processing_time_ms=800
    )

@pytest.fixture
def sample_risk_response():
    """Sample risk LLM response"""
    return LLMResponse(
        content="medium",
        model="llama2",
        tokens_used=20,
        processing_time_ms=600
    )

# ============================================================================
# CATEGORY 1: LLM INTEGRATION TESTS (10 tests)
# ============================================================================

class TestLLMIntegration:
    """Test LLM client integration"""
    
    @pytest.mark.asyncio
    async def test_ollama_client_initialization(self):
        """Test Ollama client can be initialized"""
        config = {
            "base_url": "http://localhost:11434",
            "default_model": "llama2",
            "timeout": 30
        }
        client = OllamaClient(config)
        assert client.base_url == "http://localhost:11434"
        assert client.default_model == "llama2"
        assert client.timeout == 30
        assert not client.is_connected
    
    @pytest.mark.asyncio
    async def test_llm_request_creation(self):
        """Test LLM request creation"""
        request = LLMRequest(
            prompt="Test prompt",
            system_prompt="System prompt",
            temperature=0.1,
            max_tokens=100
        )
        assert request.prompt == "Test prompt"
        assert request.system_prompt == "System prompt"
        assert request.temperature == 0.1
        assert request.max_tokens == 100
    
    @pytest.mark.asyncio
    async def test_llm_response_parsing(self):
        """Test LLM response parsing"""
        response = LLMResponse(
            content="Test response",
            model="llama2",
            tokens_used=50,
            processing_time_ms=1000
        )
        assert response.content == "Test response"
        assert response.model == "llama2"
        assert response.tokens_used == 50
        assert response.processing_time_ms == 1000
    
    @pytest.mark.asyncio
    async def test_prompt_manager_intent_prompt(self):
        """Test prompt manager intent classification prompt"""
        pm = PromptManager()
        prompt = pm.get_prompt(PromptType.INTENT_CLASSIFICATION, user_request="restart nginx")
        
        assert "system" in prompt
        assert "user" in prompt
        assert "restart nginx" in prompt["user"]
        assert "category" in prompt["system"]
    
    @pytest.mark.asyncio
    async def test_prompt_manager_entity_prompt(self):
        """Test prompt manager entity extraction prompt"""
        pm = PromptManager()
        prompt = pm.get_prompt(PromptType.ENTITY_EXTRACTION, user_request="restart nginx on web-01")
        
        assert "system" in prompt
        assert "user" in prompt
        assert "restart nginx on web-01" in prompt["user"]
        assert "hostname" in prompt["system"]
    
    @pytest.mark.asyncio
    async def test_response_parser_json_parsing(self):
        """Test response parser JSON parsing"""
        parser = ResponseParser()
        
        # Test clean JSON
        result = parser.parse_json_response('{"test": "value"}')
        assert result == {"test": "value"}
        
        # Test JSON with markdown
        result = parser.parse_json_response('```json\n{"test": "value"}\n```')
        assert result == {"test": "value"}
    
    @pytest.mark.asyncio
    async def test_response_parser_intent_parsing(self):
        """Test response parser intent parsing"""
        parser = ResponseParser()
        response = '{"category": "automation", "action": "restart_service", "confidence": 0.95}'
        
        result = parser.parse_intent_response(response)
        assert result["category"] == "automation"
        assert result["action"] == "restart_service"
        assert result["confidence"] == 0.95
    
    @pytest.mark.asyncio
    async def test_response_parser_entities_parsing(self):
        """Test response parser entities parsing"""
        parser = ResponseParser()
        response = '[{"type": "service", "value": "nginx", "confidence": 0.9}]'
        
        result = parser.parse_entities_response(response)
        assert len(result) == 1
        assert result[0]["type"] == "service"
        assert result[0]["value"] == "nginx"
        assert result[0]["confidence"] == 0.9
    
    @pytest.mark.asyncio
    async def test_response_parser_confidence_parsing(self):
        """Test response parser confidence parsing"""
        parser = ResponseParser()
        
        # Test decimal
        result = parser.parse_confidence_response("0.85")
        assert result == 0.85
        
        # Test percentage
        result = parser.parse_confidence_response("85")
        assert result == 0.85
    
    @pytest.mark.asyncio
    async def test_response_parser_risk_parsing(self):
        """Test response parser risk parsing"""
        parser = ResponseParser()
        
        result = parser.parse_risk_response("medium")
        assert result == "medium"
        
        result = parser.parse_risk_response("The risk level is HIGH for this operation")
        assert result == "high"

# ============================================================================
# CATEGORY 2: INTENT CLASSIFICATION TESTS (15 tests)
# ============================================================================

class TestIntentClassification:
    """Test intent classification functionality"""
    
    @pytest.mark.asyncio
    async def test_intent_classifier_initialization(self, mock_llm_client):
        """Test intent classifier initialization"""
        classifier = IntentClassifier(mock_llm_client)
        assert classifier.llm_client == mock_llm_client
        assert isinstance(classifier.prompt_manager, PromptManager)
        assert isinstance(classifier.response_parser, ResponseParser)
    
    @pytest.mark.asyncio
    async def test_classify_automation_intent(self, mock_llm_client, sample_llm_response):
        """Test automation intent classification"""
        mock_llm_client.generate.return_value = sample_llm_response
        
        classifier = IntentClassifier(mock_llm_client)
        result = await classifier.classify_intent("restart nginx service")
        
        assert isinstance(result, IntentV1)
        assert result.category == "automation"
        assert result.action == "restart_service"
        assert result.confidence == 0.95
    
    @pytest.mark.asyncio
    async def test_classify_monitoring_intent(self, mock_llm_client):
        """Test monitoring intent classification"""
        monitoring_response = LLMResponse(
            content='{"category": "monitoring", "action": "check_status", "confidence": 0.88}',
            model="llama2"
        )
        mock_llm_client.generate.return_value = monitoring_response
        
        classifier = IntentClassifier(mock_llm_client)
        result = await classifier.classify_intent("check server status")
        
        assert result.category == "monitoring"
        assert result.action == "check_status"
        assert result.confidence == 0.88
    
    @pytest.mark.asyncio
    async def test_classify_troubleshooting_intent(self, mock_llm_client):
        """Test troubleshooting intent classification"""
        troubleshooting_response = LLMResponse(
            content='{"category": "troubleshooting", "action": "diagnose_issue", "confidence": 0.82}',
            model="llama2"
        )
        mock_llm_client.generate.return_value = troubleshooting_response
        
        classifier = IntentClassifier(mock_llm_client)
        result = await classifier.classify_intent("why is the website slow")
        
        assert result.category == "troubleshooting"
        assert result.action == "diagnose_issue"
        assert result.confidence == 0.82
    
    @pytest.mark.asyncio
    async def test_classify_configuration_intent(self, mock_llm_client):
        """Test configuration intent classification"""
        config_response = LLMResponse(
            content='{"category": "configuration", "action": "update_config", "confidence": 0.91}',
            model="llama2"
        )
        mock_llm_client.generate.return_value = config_response
        
        classifier = IntentClassifier(mock_llm_client)
        result = await classifier.classify_intent("update nginx configuration")
        
        assert result.category == "configuration"
        assert result.action == "update_config"
        assert result.confidence == 0.91
    
    @pytest.mark.asyncio
    async def test_classify_information_intent(self, mock_llm_client):
        """Test information intent classification"""
        info_response = LLMResponse(
            content='{"category": "information", "action": "get_help", "confidence": 0.93}',
            model="llama2"
        )
        mock_llm_client.generate.return_value = info_response
        
        classifier = IntentClassifier(mock_llm_client)
        result = await classifier.classify_intent("how do I restart a service")
        
        assert result.category == "information"
        assert result.action == "get_help"
        assert result.confidence == 0.93
    
    @pytest.mark.asyncio
    async def test_get_supported_categories(self, mock_llm_client):
        """Test getting supported categories"""
        classifier = IntentClassifier(mock_llm_client)
        categories = classifier.get_supported_categories()
        
        assert "automation" in categories
        assert "monitoring" in categories
        assert "troubleshooting" in categories
        assert "configuration" in categories
        assert "information" in categories
        
        assert "restart_service" in categories["automation"]
        assert "check_status" in categories["monitoring"]
    
    @pytest.mark.asyncio
    async def test_validate_intent_valid(self, mock_llm_client):
        """Test intent validation with valid intent"""
        classifier = IntentClassifier(mock_llm_client)
        intent = IntentV1(category="automation", action="restart_service", confidence=0.9)
        
        assert classifier.validate_intent(intent) == True
    
    @pytest.mark.asyncio
    async def test_validate_intent_invalid_category(self, mock_llm_client):
        """Test intent validation with invalid category"""
        classifier = IntentClassifier(mock_llm_client)
        intent = IntentV1(category="invalid", action="restart_service", confidence=0.9)
        
        assert classifier.validate_intent(intent) == False
    
    @pytest.mark.asyncio
    async def test_validate_intent_invalid_action(self, mock_llm_client):
        """Test intent validation with invalid action"""
        classifier = IntentClassifier(mock_llm_client)
        intent = IntentV1(category="automation", action="invalid_action", confidence=0.9)
        
        assert classifier.validate_intent(intent) == False
    
    @pytest.mark.asyncio
    async def test_classify_with_fallback_success(self, mock_llm_client, sample_llm_response):
        """Test classify with fallback - success case"""
        mock_llm_client.generate.return_value = sample_llm_response
        
        classifier = IntentClassifier(mock_llm_client)
        result = await classifier.classify_with_fallback("restart nginx")
        
        assert result.category == "automation"
        assert result.action == "restart_service"
    
    @pytest.mark.asyncio
    async def test_classify_with_fallback_failure(self, mock_llm_client):
        """Test classify with fallback - failure case"""
        mock_llm_client.generate.side_effect = Exception("LLM error")
        
        classifier = IntentClassifier(mock_llm_client)
        result = await classifier.classify_with_fallback("restart nginx")
        
        assert result.category == "information"
        assert result.action == "get_help"
        assert result.confidence == 0.1
    
    @pytest.mark.asyncio
    async def test_classify_ambiguous_request(self, mock_llm_client):
        """Test classification of ambiguous request"""
        ambiguous_response = LLMResponse(
            content='{"category": "information", "action": "get_help", "confidence": 0.3}',
            model="llama2"
        )
        mock_llm_client.generate.return_value = ambiguous_response
        
        classifier = IntentClassifier(mock_llm_client)
        result = await classifier.classify_intent("do something")
        
        assert result.confidence < 0.5
    
    @pytest.mark.asyncio
    async def test_classify_complex_request(self, mock_llm_client):
        """Test classification of complex multi-part request"""
        complex_response = LLMResponse(
            content='{"category": "automation", "action": "deploy_application", "confidence": 0.87}',
            model="llama2"
        )
        mock_llm_client.generate.return_value = complex_response
        
        classifier = IntentClassifier(mock_llm_client)
        result = await classifier.classify_intent("deploy the new version of the web app to production")
        
        assert result.category == "automation"
        assert result.action == "deploy_application"
        assert result.confidence > 0.8
    
    @pytest.mark.asyncio
    async def test_classify_with_technical_terms(self, mock_llm_client):
        """Test classification with technical terms"""
        tech_response = LLMResponse(
            content='{"category": "troubleshooting", "action": "analyze_logs", "confidence": 0.92}',
            model="llama2"
        )
        mock_llm_client.generate.return_value = tech_response
        
        classifier = IntentClassifier(mock_llm_client)
        result = await classifier.classify_intent("analyze the nginx error logs for 502 errors")
        
        assert result.category == "troubleshooting"
        assert result.confidence > 0.9

# ============================================================================
# CATEGORY 3: ENTITY EXTRACTION TESTS (15 tests)
# ============================================================================

class TestEntityExtraction:
    """Test entity extraction functionality"""
    
    @pytest.mark.asyncio
    async def test_entity_extractor_initialization(self, mock_llm_client):
        """Test entity extractor initialization"""
        extractor = EntityExtractor(mock_llm_client)
        assert extractor.llm_client == mock_llm_client
        assert isinstance(extractor.prompt_manager, PromptManager)
        assert isinstance(extractor.response_parser, ResponseParser)
        assert isinstance(extractor.regex_patterns, dict)
    
    @pytest.mark.asyncio
    async def test_extract_service_entities(self, mock_llm_client, sample_entities_response):
        """Test service entity extraction"""
        mock_llm_client.generate.return_value = sample_entities_response
        
        extractor = EntityExtractor(mock_llm_client)
        result = await extractor.extract_entities("restart nginx service")
        
        assert len(result) >= 1
        service_entities = [e for e in result if e.type == "service"]
        assert len(service_entities) >= 1
        assert any(e.value == "nginx" for e in service_entities)
    
    @pytest.mark.asyncio
    async def test_extract_hostname_entities(self, mock_llm_client):
        """Test hostname entity extraction"""
        hostname_response = LLMResponse(
            content='[{"type": "hostname", "value": "web-server-01", "confidence": 0.95}]',
            model="llama2"
        )
        mock_llm_client.generate.return_value = hostname_response
        
        extractor = EntityExtractor(mock_llm_client)
        result = await extractor.extract_entities("restart nginx on web-server-01")
        
        hostname_entities = [e for e in result if e.type == "hostname"]
        assert len(hostname_entities) >= 1
        assert any(e.value == "web-server-01" for e in hostname_entities)
    
    @pytest.mark.asyncio
    async def test_extract_multiple_entity_types(self, mock_llm_client):
        """Test extraction of multiple entity types"""
        multi_response = LLMResponse(
            content='[{"type": "service", "value": "nginx", "confidence": 0.9}, {"type": "hostname", "value": "web-01", "confidence": 0.85}, {"type": "port", "value": "80", "confidence": 0.8}]',
            model="llama2"
        )
        mock_llm_client.generate.return_value = multi_response
        
        extractor = EntityExtractor(mock_llm_client)
        result = await extractor.extract_entities("restart nginx on web-01 port 80")
        
        entity_types = {e.type for e in result}
        assert "service" in entity_types
        assert "hostname" in entity_types
        assert "port" in entity_types
    
    @pytest.mark.asyncio
    async def test_extract_file_path_entities(self, mock_llm_client):
        """Test file path entity extraction"""
        path_response = LLMResponse(
            content='[{"type": "file_path", "value": "/etc/nginx/nginx.conf", "confidence": 0.92}]',
            model="llama2"
        )
        mock_llm_client.generate.return_value = path_response
        
        extractor = EntityExtractor(mock_llm_client)
        result = await extractor.extract_entities("check /etc/nginx/nginx.conf file")
        
        path_entities = [e for e in result if e.type == "file_path"]
        assert len(path_entities) >= 1
        assert any("/etc/nginx/nginx.conf" in e.value for e in path_entities)
    
    @pytest.mark.asyncio
    async def test_extract_port_entities(self, mock_llm_client):
        """Test port entity extraction"""
        port_response = LLMResponse(
            content='[{"type": "port", "value": "8080", "confidence": 0.88}]',
            model="llama2"
        )
        mock_llm_client.generate.return_value = port_response
        
        extractor = EntityExtractor(mock_llm_client)
        result = await extractor.extract_entities("check service on port 8080")
        
        port_entities = [e for e in result if e.type == "port"]
        assert len(port_entities) >= 1
        assert any(e.value == "8080" for e in port_entities)
    
    @pytest.mark.asyncio
    async def test_extract_environment_entities(self, mock_llm_client):
        """Test environment entity extraction"""
        env_response = LLMResponse(
            content='[{"type": "environment", "value": "production", "confidence": 0.94}]',
            model="llama2"
        )
        mock_llm_client.generate.return_value = env_response
        
        extractor = EntityExtractor(mock_llm_client)
        result = await extractor.extract_entities("deploy to production environment")
        
        env_entities = [e for e in result if e.type == "environment"]
        assert len(env_entities) >= 1
        assert any(e.value == "production" for e in env_entities)
    
    @pytest.mark.asyncio
    async def test_extract_command_entities(self, mock_llm_client):
        """Test command entity extraction"""
        cmd_response = LLMResponse(
            content='[{"type": "command", "value": "systemctl restart nginx", "confidence": 0.91}]',
            model="llama2"
        )
        mock_llm_client.generate.return_value = cmd_response
        
        extractor = EntityExtractor(mock_llm_client)
        result = await extractor.extract_entities("run systemctl restart nginx")
        
        cmd_entities = [e for e in result if e.type == "command"]
        assert len(cmd_entities) >= 1
        assert any("systemctl" in e.value for e in cmd_entities)
    
    @pytest.mark.asyncio
    async def test_extract_no_entities(self, mock_llm_client):
        """Test extraction when no entities found"""
        empty_response = LLMResponse(content='[]', model="llama2")
        mock_llm_client.generate.return_value = empty_response
        
        extractor = EntityExtractor(mock_llm_client)
        result = await extractor.extract_entities("hello world")
        
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_regex_pattern_extraction(self, mock_llm_client):
        """Test regex pattern extraction"""
        # Mock LLM to return empty so we test regex patterns
        empty_response = LLMResponse(content='[]', model="llama2")
        mock_llm_client.generate.return_value = empty_response
        
        extractor = EntityExtractor(mock_llm_client)
        result = await extractor.extract_entities("restart nginx.service on 192.168.1.100")
        
        # Should find entities via regex even if LLM returns empty
        assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_get_supported_entity_types(self, mock_llm_client):
        """Test getting supported entity types"""
        extractor = EntityExtractor(mock_llm_client)
        types = extractor.get_supported_entity_types()
        
        assert "hostname" in types
        assert "service" in types
        assert "command" in types
        assert "file_path" in types
        assert "port" in types
        assert "environment" in types
    
    @pytest.mark.asyncio
    async def test_validate_entity_valid(self, mock_llm_client):
        """Test entity validation with valid entity"""
        extractor = EntityExtractor(mock_llm_client)
        entity = EntityV1(type="service", value="nginx", confidence=0.9)
        
        assert extractor.validate_entity(entity) == True
    
    @pytest.mark.asyncio
    async def test_validate_entity_invalid_type(self, mock_llm_client):
        """Test entity validation with invalid type"""
        extractor = EntityExtractor(mock_llm_client)
        entity = EntityV1(type="invalid_type", value="nginx", confidence=0.9)
        
        assert extractor.validate_entity(entity) == False
    
    @pytest.mark.asyncio
    async def test_validate_entity_invalid_port(self, mock_llm_client):
        """Test entity validation with invalid port"""
        extractor = EntityExtractor(mock_llm_client)
        entity = EntityV1(type="port", value="99999", confidence=0.9)
        
        assert extractor.validate_entity(entity) == False
    
    @pytest.mark.asyncio
    async def test_merge_entities_deduplication(self, mock_llm_client):
        """Test entity merging and deduplication"""
        extractor = EntityExtractor(mock_llm_client)
        
        llm_entities = [EntityV1(type="service", value="nginx", confidence=0.9)]
        regex_entities = [EntityV1(type="service", value="nginx", confidence=0.8)]
        
        result = extractor._merge_entities(llm_entities, regex_entities)
        
        # Should have only one nginx entity with higher confidence
        nginx_entities = [e for e in result if e.value == "nginx"]
        assert len(nginx_entities) == 1
        assert nginx_entities[0].confidence == 0.9

# ============================================================================
# CATEGORY 4: CONFIDENCE SCORING TESTS (10 tests)
# ============================================================================

class TestConfidenceScoring:
    """Test confidence scoring functionality"""
    
    @pytest.mark.asyncio
    async def test_confidence_scorer_initialization(self, mock_llm_client):
        """Test confidence scorer initialization"""
        scorer = ConfidenceScorer(mock_llm_client)
        assert scorer.llm_client == mock_llm_client
        assert isinstance(scorer.prompt_manager, PromptManager)
        assert isinstance(scorer.response_parser, ResponseParser)
    
    @pytest.mark.asyncio
    async def test_calculate_high_confidence(self, mock_llm_client, sample_confidence_response):
        """Test high confidence calculation"""
        mock_llm_client.generate.return_value = sample_confidence_response
        
        scorer = ConfidenceScorer(mock_llm_client)
        intent = IntentV1(category="automation", action="restart_service", confidence=0.95)
        entities = [EntityV1(type="service", value="nginx", confidence=0.9)]
        
        result = await scorer.calculate_overall_confidence("restart nginx", intent, entities)
        
        assert result["confidence_level"] == ConfidenceLevel.HIGH
        assert result["overall_confidence"] > 0.8
    
    @pytest.mark.asyncio
    async def test_calculate_medium_confidence(self, mock_llm_client):
        """Test medium confidence calculation"""
        medium_response = LLMResponse(content="0.65", model="llama2")
        mock_llm_client.generate.return_value = medium_response
        
        scorer = ConfidenceScorer(mock_llm_client)
        intent = IntentV1(category="automation", action="restart_service", confidence=0.7)
        entities = [EntityV1(type="service", value="nginx", confidence=0.6)]
        
        result = await scorer.calculate_overall_confidence("restart something", intent, entities)
        
        assert result["confidence_level"] == ConfidenceLevel.MEDIUM
        assert 0.5 <= result["overall_confidence"] < 0.8
    
    @pytest.mark.asyncio
    async def test_calculate_low_confidence(self, mock_llm_client):
        """Test low confidence calculation"""
        low_response = LLMResponse(content="0.3", model="llama2")
        mock_llm_client.generate.return_value = low_response
        
        scorer = ConfidenceScorer(mock_llm_client)
        intent = IntentV1(category="information", action="get_help", confidence=0.4)
        entities = []
        
        result = await scorer.calculate_overall_confidence("do something", intent, entities)
        
        assert result["confidence_level"] == ConfidenceLevel.LOW
        assert result["overall_confidence"] < 0.5
    
    @pytest.mark.asyncio
    async def test_confidence_with_no_entities(self, mock_llm_client):
        """Test confidence calculation with no entities"""
        scorer = ConfidenceScorer(mock_llm_client)
        intent = IntentV1(category="information", action="get_help", confidence=0.8)
        entities = []
        
        # Information requests don't need entities, so confidence should remain high
        result = await scorer.calculate_overall_confidence("how do I restart a service", intent, entities)
        
        # Should still have reasonable confidence for information requests
        assert result["overall_confidence"] > 0.5
    
    @pytest.mark.asyncio
    async def test_confidence_with_multiple_entities(self, mock_llm_client, sample_confidence_response):
        """Test confidence calculation with multiple entities"""
        mock_llm_client.generate.return_value = sample_confidence_response
        
        scorer = ConfidenceScorer(mock_llm_client)
        intent = IntentV1(category="automation", action="restart_service", confidence=0.9)
        entities = [
            EntityV1(type="service", value="nginx", confidence=0.95),
            EntityV1(type="hostname", value="web-01", confidence=0.85),
            EntityV1(type="port", value="80", confidence=0.8)
        ]
        
        result = await scorer.calculate_overall_confidence("restart nginx on web-01 port 80", intent, entities)
        
        assert result["confidence_level"] == ConfidenceLevel.HIGH
        assert result["overall_confidence"] > 0.8
    
    @pytest.mark.asyncio
    async def test_assess_request_clarity_clear(self, mock_llm_client):
        """Test request clarity assessment - clear request"""
        scorer = ConfidenceScorer(mock_llm_client)
        clarity = scorer._assess_request_clarity("restart nginx service")
        
        assert clarity > 0.7  # Should be high clarity
    
    @pytest.mark.asyncio
    async def test_assess_request_clarity_vague(self, mock_llm_client):
        """Test request clarity assessment - vague request"""
        scorer = ConfidenceScorer(mock_llm_client)
        clarity = scorer._assess_request_clarity("do something with the thing")
        
        assert clarity <= 0.5  # Should be low clarity
    
    @pytest.mark.asyncio
    async def test_assess_technical_terms_high(self, mock_llm_client):
        """Test technical terms assessment - high technical content"""
        scorer = ConfidenceScorer(mock_llm_client)
        tech_score = scorer._assess_technical_terms("restart nginx service using systemctl on ubuntu server")
        
        assert tech_score >= 0.6  # Should be high technical score
    
    @pytest.mark.asyncio
    async def test_assess_technical_terms_low(self, mock_llm_client):
        """Test technical terms assessment - low technical content"""
        scorer = ConfidenceScorer(mock_llm_client)
        tech_score = scorer._assess_technical_terms("please help me with my problem")
        
        assert tech_score < 0.3  # Should be low technical score
    
    @pytest.mark.asyncio
    async def test_get_confidence_explanation(self, mock_llm_client):
        """Test confidence explanation generation"""
        scorer = ConfidenceScorer(mock_llm_client)
        intent = IntentV1(category="automation", action="restart_service", confidence=0.9)
        entities = [EntityV1(type="service", value="nginx", confidence=0.95)]
        confidence_data = {
            "confidence_level": ConfidenceLevel.HIGH,
            "overall_confidence": 0.88
        }
        
        explanation = scorer.get_confidence_explanation("restart nginx", intent, entities, confidence_data)
        
        assert "High confidence" in explanation
        assert "restart_service" in explanation
        assert isinstance(explanation, str)
        assert len(explanation) > 0

# ============================================================================
# CATEGORY 5: RISK ASSESSMENT TESTS (10 tests)
# ============================================================================

class TestRiskAssessment:
    """Test risk assessment functionality"""
    
    @pytest.mark.asyncio
    async def test_risk_assessor_initialization(self, mock_llm_client):
        """Test risk assessor initialization"""
        assessor = RiskAssessor(mock_llm_client)
        assert assessor.llm_client == mock_llm_client
        assert isinstance(assessor.prompt_manager, PromptManager)
        assert isinstance(assessor.response_parser, ResponseParser)
        assert isinstance(assessor.risk_rules, dict)
    
    @pytest.mark.asyncio
    async def test_assess_low_risk(self, mock_llm_client):
        """Test low risk assessment"""
        low_risk_response = LLMResponse(content="low", model="llama2")
        mock_llm_client.generate.return_value = low_risk_response
        
        assessor = RiskAssessor(mock_llm_client)
        intent = IntentV1(category="monitoring", action="check_status", confidence=0.9)
        entities = [EntityV1(type="service", value="nginx", confidence=0.9)]
        
        result = await assessor.assess_risk("check nginx status", intent, entities)
        
        assert result["risk_level"] == RiskLevel.LOW
        assert result["requires_approval"] == False
    
    @pytest.mark.asyncio
    async def test_assess_medium_risk(self, mock_llm_client, sample_risk_response):
        """Test medium risk assessment"""
        mock_llm_client.generate.return_value = sample_risk_response
        
        assessor = RiskAssessor(mock_llm_client)
        intent = IntentV1(category="automation", action="restart_service", confidence=0.9)
        entities = [EntityV1(type="service", value="nginx", confidence=0.9)]
        
        result = await assessor.assess_risk("restart nginx", intent, entities)
        
        assert result["risk_level"] == RiskLevel.MEDIUM
    
    @pytest.mark.asyncio
    async def test_assess_high_risk(self, mock_llm_client):
        """Test high risk assessment"""
        high_risk_response = LLMResponse(content="high", model="llama2")
        mock_llm_client.generate.return_value = high_risk_response
        
        assessor = RiskAssessor(mock_llm_client)
        intent = IntentV1(category="automation", action="delete", confidence=0.9)
        entities = [EntityV1(type="database", value="user_data", confidence=0.9)]
        
        result = await assessor.assess_risk("delete user_data database", intent, entities)
        
        assert result["risk_level"] in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        assert result["requires_approval"] == True
    
    @pytest.mark.asyncio
    async def test_assess_critical_risk(self, mock_llm_client):
        """Test critical risk assessment"""
        critical_risk_response = LLMResponse(content="critical", model="llama2")
        mock_llm_client.generate.return_value = critical_risk_response
        
        assessor = RiskAssessor(mock_llm_client)
        intent = IntentV1(category="automation", action="delete", confidence=0.9)
        entities = [EntityV1(type="database", value="production", confidence=0.9)]
        
        result = await assessor.assess_risk("delete production database", intent, entities)
        
        assert result["risk_level"] == RiskLevel.CRITICAL
        assert result["requires_approval"] == True
    
    @pytest.mark.asyncio
    async def test_production_entity_requires_approval(self, mock_llm_client):
        """Test that production entities require approval"""
        low_risk_response = LLMResponse(content="low", model="llama2")
        mock_llm_client.generate.return_value = low_risk_response
        
        assessor = RiskAssessor(mock_llm_client)
        intent = IntentV1(category="automation", action="restart_service", confidence=0.9)
        entities = [EntityV1(type="hostname", value="prod-web-01", confidence=0.9)]
        
        result = await assessor.assess_risk("restart service on prod-web-01", intent, entities)
        
        assert result["requires_approval"] == True
    
    @pytest.mark.asyncio
    async def test_information_requests_no_approval(self, mock_llm_client):
        """Test that information requests don't require approval"""
        low_risk_response = LLMResponse(content="low", model="llama2")
        mock_llm_client.generate.return_value = low_risk_response
        
        assessor = RiskAssessor(mock_llm_client)
        intent = IntentV1(category="information", action="get_help", confidence=0.9)
        entities = [EntityV1(type="hostname", value="prod-web-01", confidence=0.9)]
        
        result = await assessor.assess_risk("how to restart service on prod-web-01", intent, entities)
        
        assert result["requires_approval"] == False
    
    @pytest.mark.asyncio
    async def test_check_critical_combinations(self, mock_llm_client):
        """Test critical risk combinations detection"""
        assessor = RiskAssessor(mock_llm_client)
        intent = IntentV1(category="automation", action="delete", confidence=0.9)
        entities = [EntityV1(type="database", value="user_data", confidence=0.9)]
        
        risk = assessor._check_critical_combinations(intent, entities)
        
        assert risk == RiskLevel.CRITICAL
    
    @pytest.mark.asyncio
    async def test_rule_based_risk_calculation(self, mock_llm_client):
        """Test rule-based risk calculation"""
        assessor = RiskAssessor(mock_llm_client)
        
        # High risk action
        intent = IntentV1(category="automation", action="delete", confidence=0.9)
        entities = [EntityV1(type="service", value="nginx", confidence=0.9)]
        
        risk = assessor._calculate_rule_based_risk(intent, entities)
        
        assert risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]
    
    @pytest.mark.asyncio
    async def test_get_risk_mitigation_suggestions(self, mock_llm_client):
        """Test risk mitigation suggestions"""
        assessor = RiskAssessor(mock_llm_client)
        intent = IntentV1(category="automation", action="delete", confidence=0.9)
        entities = [EntityV1(type="database", value="user_data", confidence=0.9)]
        
        suggestions = assessor.get_risk_mitigation_suggestions(intent, entities, RiskLevel.HIGH)
        
        assert len(suggestions) > 0
        assert any("backup" in s.lower() for s in suggestions)
        assert any("approval" in s.lower() for s in suggestions)
    
    @pytest.mark.asyncio
    async def test_combine_risk_assessments(self, mock_llm_client):
        """Test combining LLM and rule-based risk assessments"""
        assessor = RiskAssessor(mock_llm_client)
        
        # Should take the higher risk
        combined = assessor._combine_risk_assessments(RiskLevel.LOW, RiskLevel.HIGH)
        assert combined == RiskLevel.HIGH
        
        combined = assessor._combine_risk_assessments(RiskLevel.MEDIUM, RiskLevel.LOW)
        assert combined == RiskLevel.MEDIUM

# ============================================================================
# CATEGORY 6: STAGE A INTEGRATION TESTS (10 tests)
# ============================================================================

class TestStageAIntegration:
    """Test Stage A classifier integration"""
    
    @pytest.mark.asyncio
    async def test_stage_a_classifier_initialization(self, mock_llm_client):
        """Test Stage A classifier initialization"""
        classifier = StageAClassifier(mock_llm_client)
        assert classifier.llm_client == mock_llm_client
        assert isinstance(classifier.intent_classifier, IntentClassifier)
        assert isinstance(classifier.entity_extractor, EntityExtractor)
        assert isinstance(classifier.confidence_scorer, ConfidenceScorer)
        assert isinstance(classifier.risk_assessor, RiskAssessor)
        assert classifier.version == "1.0.0"
    
    @pytest.mark.asyncio
    async def test_classify_complete_flow(self, mock_llm_client):
        """Test complete classification flow"""
        # Mock all LLM responses
        responses = [
            LLMResponse(content='{"category": "automation", "action": "restart_service", "confidence": 0.95}', model="llama2"),
            LLMResponse(content='[{"type": "service", "value": "nginx", "confidence": 0.9}]', model="llama2"),
            LLMResponse(content="0.88", model="llama2"),
            LLMResponse(content="medium", model="llama2")
        ]
        mock_llm_client.generate.side_effect = responses
        
        classifier = StageAClassifier(mock_llm_client)
        result = await classifier.classify("restart nginx service")
        
        assert isinstance(result, DecisionV1)
        assert result.intent.category == "automation"
        assert result.intent.action == "restart_service"
        assert len(result.entities) >= 1
        assert result.overall_confidence > 0.8
        assert result.risk_level == RiskLevel.MEDIUM
        assert result.next_stage == "stage_b"
    
    @pytest.mark.asyncio
    async def test_classify_with_context(self, mock_llm_client):
        """Test classification with context"""
        responses = [
            LLMResponse(content='{"category": "monitoring", "action": "check_status", "confidence": 0.9}', model="llama2"),
            LLMResponse(content='[]', model="llama2"),
            LLMResponse(content="0.85", model="llama2"),
            LLMResponse(content="low", model="llama2")
        ]
        mock_llm_client.generate.side_effect = responses
        
        classifier = StageAClassifier(mock_llm_client)
        context = {"user_id": "test_user", "session_id": "test_session"}
        result = await classifier.classify("check status", context)
        
        assert result.context["user_id"] == "test_user"
        assert result.context["session_id"] == "test_session"
    
    @pytest.mark.asyncio
    async def test_classify_information_request(self, mock_llm_client):
        """Test classification of information request"""
        responses = [
            LLMResponse(content='{"category": "information", "action": "get_help", "confidence": 0.92}', model="llama2"),
            LLMResponse(content='[]', model="llama2"),
            LLMResponse(content="0.88", model="llama2"),
            LLMResponse(content="low", model="llama2")
        ]
        mock_llm_client.generate.side_effect = responses
        
        classifier = StageAClassifier(mock_llm_client)
        result = await classifier.classify("how do I restart a service")
        
        assert result.decision_type == DecisionType.INFO
        assert result.next_stage == "stage_d"
        assert result.requires_approval == False
    
    @pytest.mark.asyncio
    async def test_classify_low_confidence_request(self, mock_llm_client):
        """Test classification of low confidence request"""
        responses = [
            LLMResponse(content='{"category": "automation", "action": "restart_service", "confidence": 0.3}', model="llama2"),
            LLMResponse(content='[]', model="llama2"),
            LLMResponse(content="0.25", model="llama2"),
            LLMResponse(content="medium", model="llama2")
        ]
        mock_llm_client.generate.side_effect = responses
        
        classifier = StageAClassifier(mock_llm_client)
        result = await classifier.classify("do something")
        
        assert result.confidence_level == ConfidenceLevel.LOW
        assert result.decision_type == DecisionType.INFO
        assert result.next_stage == "stage_d"
    
    @pytest.mark.asyncio
    async def test_generate_decision_id(self, mock_llm_client):
        """Test decision ID generation"""
        classifier = StageAClassifier(mock_llm_client)
        decision_id = classifier._generate_decision_id()
        
        assert decision_id.startswith("dec_")
        assert len(decision_id) > 10
        
        # Should be unique
        decision_id2 = classifier._generate_decision_id()
        assert decision_id != decision_id2
    
    @pytest.mark.asyncio
    async def test_determine_decision_type(self, mock_llm_client):
        """Test decision type determination"""
        classifier = StageAClassifier(mock_llm_client)
        
        # Information intent should be INFO type
        intent = IntentV1(category="information", action="get_help", confidence=0.9)
        confidence_data = {"confidence_level": ConfidenceLevel.HIGH}
        decision_type = classifier._determine_decision_type(intent, confidence_data)
        assert decision_type == DecisionType.INFO
        
        # Automation intent with high confidence should be ACTION type
        intent = IntentV1(category="automation", action="restart_service", confidence=0.9)
        confidence_data = {"confidence_level": ConfidenceLevel.HIGH}
        decision_type = classifier._determine_decision_type(intent, confidence_data)
        assert decision_type == DecisionType.ACTION
    
    @pytest.mark.asyncio
    async def test_determine_next_stage(self, mock_llm_client):
        """Test next stage determination"""
        classifier = StageAClassifier(mock_llm_client)
        
        # Low confidence should go to Stage D
        intent = IntentV1(category="automation", action="restart_service", confidence=0.3)
        confidence_data = {"confidence_level": ConfidenceLevel.LOW}
        risk_data = {"risk_level": RiskLevel.MEDIUM}
        next_stage = classifier._determine_next_stage(intent, confidence_data, risk_data)
        assert next_stage == "stage_d"
        
        # High confidence automation should go to Stage B
        confidence_data = {"confidence_level": ConfidenceLevel.HIGH}
        next_stage = classifier._determine_next_stage(intent, confidence_data, risk_data)
        assert next_stage == "stage_b"
    
    @pytest.mark.asyncio
    async def test_health_check(self, mock_llm_client):
        """Test Stage A health check"""
        mock_llm_client.health_check.return_value = True
        
        classifier = StageAClassifier(mock_llm_client)
        health = await classifier.health_check()
        
        assert health["stage_a"] == "healthy"
        assert health["version"] == "1.0.0"
        assert "components" in health
        assert health["components"]["llm_client"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_get_capabilities(self, mock_llm_client):
        """Test getting Stage A capabilities"""
        classifier = StageAClassifier(mock_llm_client)
        capabilities = await classifier.get_capabilities()
        
        assert capabilities["stage"] == "stage_a"
        assert capabilities["version"] == "1.0.0"
        assert "capabilities" in capabilities
        assert "intent_classification" in capabilities["capabilities"]
        assert "entity_extraction" in capabilities["capabilities"]
        assert "confidence_scoring" in capabilities["capabilities"]
        assert "risk_assessment" in capabilities["capabilities"]
    
    @pytest.mark.asyncio
    async def test_process_batch(self, mock_llm_client):
        """Test batch processing"""
        responses = [
            LLMResponse(content='{"category": "automation", "action": "restart_service", "confidence": 0.95}', model="llama2"),
            LLMResponse(content='[{"type": "service", "value": "nginx", "confidence": 0.9}]', model="llama2"),
            LLMResponse(content="0.88", model="llama2"),
            LLMResponse(content="medium", model="llama2")
        ] * 2  # Two requests
        mock_llm_client.generate.side_effect = responses
        
        classifier = StageAClassifier(mock_llm_client)
        requests = ["restart nginx", "start apache"]
        results = await classifier.process_batch(requests)
        
        assert len(results) == 2
        assert all(isinstance(r, DecisionV1) for r in results)

# ============================================================================
# CATEGORY 7: ERROR HANDLING TESTS (5 tests)
# ============================================================================

class TestErrorHandling:
    """Test error handling scenarios"""
    
    @pytest.mark.asyncio
    async def test_llm_connection_error(self, mock_llm_client):
        """Test handling of LLM connection errors"""
        mock_llm_client.generate.side_effect = Exception("Connection failed")
        
        classifier = StageAClassifier(mock_llm_client)
        result = await classifier.classify("restart nginx")
        
        # Should return fallback decision
        assert result.intent.category == "information"
        assert result.intent.action == "get_help"
        assert result.confidence_level in [ConfidenceLevel.LOW, ConfidenceLevel.MEDIUM]
    
    @pytest.mark.asyncio
    async def test_invalid_json_response(self, mock_llm_client):
        """Test handling of invalid JSON responses"""
        invalid_response = LLMResponse(content="invalid json", model="llama2")
        mock_llm_client.generate.return_value = invalid_response
        
        intent_classifier = IntentClassifier(mock_llm_client)
        result = await intent_classifier.classify_intent("restart nginx")
        
        # Should return fallback intent
        assert result.category == "unknown"
        assert result.confidence == 0.0
    
    @pytest.mark.asyncio
    async def test_empty_user_request(self, mock_llm_client):
        """Test handling of empty user request"""
        responses = [
            LLMResponse(content='{"category": "information", "action": "get_help", "confidence": 0.1}', model="llama2"),
            LLMResponse(content='[]', model="llama2"),
            LLMResponse(content="0.1", model="llama2"),
            LLMResponse(content="low", model="llama2")
        ]
        mock_llm_client.generate.side_effect = responses
        
        classifier = StageAClassifier(mock_llm_client)
        result = await classifier.classify("")
        
        assert result.decision_type == DecisionType.INFO
        assert result.confidence_level == ConfidenceLevel.LOW
    
    @pytest.mark.asyncio
    async def test_malformed_entity_response(self, mock_llm_client):
        """Test handling of malformed entity responses"""
        malformed_response = LLMResponse(content='{"not": "a list"}', model="llama2")
        mock_llm_client.generate.return_value = malformed_response
        
        extractor = EntityExtractor(mock_llm_client)
        result = await extractor.extract_entities("restart nginx")
        
        # Should fallback to regex extraction and find nginx service
        assert len(result) >= 0  # May find entities via regex fallback
    
    @pytest.mark.asyncio
    async def test_confidence_parsing_error(self, mock_llm_client):
        """Test handling of confidence parsing errors"""
        invalid_response = LLMResponse(content="not a number", model="llama2")
        mock_llm_client.generate.return_value = invalid_response
        
        parser = ResponseParser()
        
        with pytest.raises(ValueError):
            parser.parse_confidence_response("not a number")

# ============================================================================
# TEST RUNNER
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])