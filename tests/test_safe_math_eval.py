"""
Unit tests for Safe Math Evaluator

Tests the security and functionality of the safe expression evaluator.
"""

import pytest
import math
from pipeline.stages.stage_b.safe_math_eval import SafeMathEvaluator, safe_eval


class TestSafeMathEvaluator:
    """Test safe math expression evaluation"""
    
    def test_simple_arithmetic(self):
        """Test basic arithmetic operations"""
        evaluator = SafeMathEvaluator()
        
        assert evaluator.evaluate("1 + 2", {}) == 3.0
        assert evaluator.evaluate("10 - 3", {}) == 7.0
        assert evaluator.evaluate("4 * 5", {}) == 20.0
        assert evaluator.evaluate("20 / 4", {}) == 5.0
        assert evaluator.evaluate("7 // 2", {}) == 3.0
        assert evaluator.evaluate("10 % 3", {}) == 1.0
        assert evaluator.evaluate("2 ** 3", {}) == 8.0
    
    def test_variables(self):
        """Test variable substitution"""
        evaluator = SafeMathEvaluator()
        context = {'N': 100, 'pages': 5}
        
        assert evaluator.evaluate("N", context) == 100.0
        assert evaluator.evaluate("N + 10", context) == 110.0
        assert evaluator.evaluate("N * pages", context) == 500.0
        assert evaluator.evaluate("120 + 0.02 * N", context) == 122.0
    
    def test_functions(self):
        """Test mathematical functions"""
        evaluator = SafeMathEvaluator()
        context = {'N': 100}
        
        result = evaluator.evaluate("log(N)", context)
        assert abs(result - math.log(100)) < 0.001
        
        result = evaluator.evaluate("sqrt(N)", context)
        assert result == 10.0
        
        result = evaluator.evaluate("min(N, 50)", context)
        assert result == 50.0
        
        result = evaluator.evaluate("max(N, 200)", context)
        assert result == 200.0
        
        result = evaluator.evaluate("abs(-42)", context)
        assert result == 42.0
    
    def test_complex_expressions(self):
        """Test complex nested expressions"""
        evaluator = SafeMathEvaluator()
        context = {'N': 100, 'p95_latency': 150}
        
        # Time estimate formula
        result = evaluator.evaluate("3000 + 400 * log(N)", context)
        expected = 3000 + 400 * math.log(100)
        assert abs(result - expected) < 0.001
        
        # Normalization formula
        result = evaluator.evaluate("1 / (1 + N / 1000)", context)
        expected = 1 / (1 + 100 / 1000)
        assert abs(result - expected) < 0.001
        
        # Multi-variable
        result = evaluator.evaluate("3000 + 400 * log(N) + p95_latency * 1.2", context)
        expected = 3000 + 400 * math.log(100) + 150 * 1.2
        assert abs(result - expected) < 0.001
    
    def test_constants(self):
        """Test mathematical constants"""
        evaluator = SafeMathEvaluator()
        
        result = evaluator.evaluate("pi", {})
        assert abs(result - math.pi) < 0.001
        
        result = evaluator.evaluate("e", {})
        assert abs(result - math.e) < 0.001
        
        result = evaluator.evaluate("2 * pi", {})
        assert abs(result - 2 * math.pi) < 0.001
    
    def test_numeric_input(self):
        """Test that numeric inputs are passed through"""
        evaluator = SafeMathEvaluator()
        
        assert evaluator.evaluate(42, {}) == 42.0
        assert evaluator.evaluate(3.14, {}) == 3.14
        assert evaluator.evaluate(100, {}) == 100.0
    
    def test_default_variables(self):
        """Test default variable values"""
        evaluator = SafeMathEvaluator()
        
        # Should use default N=0
        result = evaluator.evaluate("N + 10", {})
        assert result == 10.0
        
        # Should use default pages=1
        result = evaluator.evaluate("pages * 100", {})
        assert result == 100.0
    
    def test_security_no_imports(self):
        """Test that imports are blocked"""
        evaluator = SafeMathEvaluator()
        
        with pytest.raises((ValueError, SyntaxError)):
            evaluator.evaluate("__import__('os').system('ls')", {})
    
    def test_security_no_exec(self):
        """Test that exec/eval are blocked"""
        evaluator = SafeMathEvaluator()
        
        with pytest.raises((ValueError, SyntaxError)):
            evaluator.evaluate("exec('print(1)')", {})
        
        with pytest.raises((ValueError, SyntaxError)):
            evaluator.evaluate("eval('1+1')", {})
    
    def test_security_no_file_access(self):
        """Test that file operations are blocked"""
        evaluator = SafeMathEvaluator()
        
        with pytest.raises((ValueError, SyntaxError)):
            evaluator.evaluate("open('/etc/passwd')", {})
    
    def test_security_no_attribute_access(self):
        """Test that attribute access is blocked"""
        evaluator = SafeMathEvaluator()
        
        with pytest.raises((ValueError, SyntaxError)):
            evaluator.evaluate("N.__class__", {'N': 100})
    
    def test_security_no_list_comprehension(self):
        """Test that list comprehensions are blocked"""
        evaluator = SafeMathEvaluator()
        
        with pytest.raises((ValueError, SyntaxError)):
            evaluator.evaluate("[x for x in range(10)]", {})
    
    def test_security_disallowed_functions(self):
        """Test that disallowed functions are blocked"""
        evaluator = SafeMathEvaluator()
        
        with pytest.raises(ValueError, match="not allowed"):
            evaluator.evaluate("print(1)", {})
        
        with pytest.raises(ValueError, match="not allowed"):
            evaluator.evaluate("len([1,2,3])", {})
    
    def test_error_division_by_zero(self):
        """Test division by zero handling"""
        evaluator = SafeMathEvaluator()
        
        with pytest.raises(ValueError, match="Division by zero"):
            evaluator.evaluate("10 / 0", {})
        
        with pytest.raises(ValueError, match="Division by zero"):
            evaluator.evaluate("10 // 0", {})
    
    def test_error_undefined_variable(self):
        """Test undefined variable handling"""
        evaluator = SafeMathEvaluator()
        
        with pytest.raises(ValueError, match="not defined"):
            evaluator.evaluate("undefined_var + 10", {})
    
    def test_error_invalid_syntax(self):
        """Test invalid syntax handling"""
        evaluator = SafeMathEvaluator()
        
        with pytest.raises(SyntaxError):
            evaluator.evaluate("1 +", {})
        
        with pytest.raises(SyntaxError):
            evaluator.evaluate("* 5", {})
    
    def test_error_exponent_too_large(self):
        """Test that huge exponents are blocked"""
        evaluator = SafeMathEvaluator()
        
        with pytest.raises(ValueError, match="Exponent too large"):
            evaluator.evaluate("2 ** 1000", {})
    
    def test_error_max_depth(self):
        """Test maximum nesting depth"""
        evaluator = SafeMathEvaluator(max_depth=5)
        
        # This should work (depth 3)
        evaluator.evaluate("1 + (2 + (3 + 4))", {})
        
        # This should fail (depth > 5)
        with pytest.raises(ValueError, match="too deeply nested"):
            evaluator.evaluate("1+(2+(3+(4+(5+(6+(7+8))))))", {})
    
    def test_convenience_function(self):
        """Test convenience function"""
        result = safe_eval("100 + 20", {})
        assert result == 120.0
        
        result = safe_eval(42, {})
        assert result == 42.0
        
        result = safe_eval("N * 2", {'N': 50})
        assert result == 100.0


class TestRealWorldExpressions:
    """Test real-world expressions from optimization profiles"""
    
    def test_asset_service_query_count(self):
        """Test asset-service-query count pattern"""
        context = {'N': 1000}
        result = safe_eval("120 + 0.02 * N", context)
        assert result == 140.0
    
    def test_asset_service_query_list(self):
        """Test asset-service-query list pattern"""
        context = {'N': 500, 'pages': 5}
        result = safe_eval("200 + 2 * N + 500 * pages", context)
        assert result == 3700.0
    
    def test_asset_direct_poll_parallel(self):
        """Test asset-direct-poll parallel pattern"""
        context = {'N': 100, 'p95_latency': 150}
        result = safe_eval("3000 + 400 * log(N) + p95_latency * 1.2", context)
        expected = 3000 + 400 * math.log(100) + 150 * 1.2
        assert abs(result - expected) < 0.001
    
    def test_normalization_formula(self):
        """Test feature normalization formulas"""
        # Speed normalization (inverse)
        context = {'time_ms': 1000}
        result = safe_eval("1 / (1 + time_ms / 1000)", context)
        assert abs(result - 0.5) < 0.001
        
        # Cost normalization
        context = {'cost': 100}
        result = safe_eval("1 / (1 + cost / 10)", context)
        assert abs(result - 1/11) < 0.001
    
    def test_policy_conditions(self):
        """Test policy condition expressions"""
        evaluator = SafeMathEvaluator()
        
        # N > 50
        context = {'N': 100}
        result = evaluator.evaluate("N", context)
        assert result > 50
        
        # cost > budget
        context = {'cost': 150}
        result = evaluator.evaluate("cost", context)
        assert result > 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])