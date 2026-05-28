from pipeline.pandoc_ast_builder import build_pandoc_ast

def test_build_pandoc_ast_math_display():
    doc = {
        "sections": [
            {
                "level": 1,
                "title": "Teste STEM",
                "blocks": [
                    {
                        "type": "math",
                        "text": "E = mc^2",
                        "display": True
                    }
                ]
            }
        ]
    }
    
    ast = build_pandoc_ast(doc)
    
    # Encontra o bloco de matemática no AST do Pandoc
    # Estrutura: ast["blocks"] -> Header, depois Para com Math
    math_block = ast["blocks"][1]
    assert math_block["t"] == "Para"
    
    math_inline = math_block["c"][0]
    assert math_inline["t"] == "Math"
    assert math_inline["c"][0]["t"] == "DisplayMath"
    assert math_inline["c"][1] == "E = mc^2"

def test_build_pandoc_ast_math_inline():
    doc = {
        "sections": [
            {
                "level": 1,
                "title": "Teste STEM",
                "blocks": [
                    {
                        "type": "math",
                        "text": "x+y",
                        "display": False
                    }
                ]
            }
        ]
    }
    
    ast = build_pandoc_ast(doc)
    
    math_block = ast["blocks"][1]
    math_inline = math_block["c"][0]
    assert math_inline["c"][0]["t"] == "InlineMath"
    assert math_inline["c"][1] == "x+y"
