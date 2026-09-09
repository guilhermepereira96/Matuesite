from typing import Optional

from fastapi import FastAPI, HTTPException, status, Response
from pydantic import BaseModel, Field
import uvicorn


app = FastAPI(title="API de Produtos - Exercícios Práticos")


# Banco de dados em memória
produtos_db = {
    1: {
        "nome": "Teclado",
        "preco": 100.0,
        "estoque": 10,
        "em_estoque": True,
        "ativo": True
    },
    2: {
        "nome": "Monitor",
        "preco": 1000.0,
        "estoque": 5,
        "em_estoque": False,
        "ativo": True
    }
}


# Página inicial da aplicação
@app.get("/")
def inicio():
    return {
        "mensagem": "API Matuesite funcionando no Azure, atualização 09/09!!"
    }


# Modelo usado em POST e PUT
class ProdutoSchema(BaseModel):
    nome: str
    preco: float = Field(
        gt=0,
        description="O preço deve ser maior que zero"
    )
    estoque: int = Field(
        ge=0,
        description="O estoque não pode ser negativo"
    )
    em_estoque: bool = True
    ativo: bool = True


# Modelo usado no PATCH
class ProdutoPatchSchema(BaseModel):
    nome: Optional[str] = None
    preco: Optional[float] = Field(None, gt=0)
    estoque: Optional[int] = Field(None, ge=0)
    em_estoque: Optional[bool] = None
    ativo: Optional[bool] = None


# Buscar produto por ID
@app.get("/produtos/{produto_id}")
def obter_produto(produto_id: int):

    if produto_id not in produtos_db:
        raise HTTPException(
            status_code=404,
            detail="Produto não encontrado."
        )

    return produtos_db[produto_id]


# Criar produto
@app.post(
    "/produtos/",
    status_code=status.HTTP_201_CREATED
)
def criar_produto(produto: ProdutoSchema):

    novo_id = max(produtos_db.keys()) + 1 if produtos_db else 1

    produtos_db[novo_id] = produto.model_dump()

    return {
        "id": novo_id,
        **produtos_db[novo_id]
    }


# PUT - substituição completa
@app.put("/produtos/perigoso/{produto_id}")
def atualizar_produto_perigoso(
    produto_id: int,
    produto: ProdutoSchema
):

    if produto_id not in produtos_db:
        raise HTTPException(
            status_code=404,
            detail="Produto não encontrado."
        )

    produtos_db[produto_id] = produto.model_dump()

    return {
        "mensagem": "Substituição concluída.",
        "produto": produtos_db[produto_id]
    }


# PATCH - atualização parcial
@app.patch("/produtos/{produto_id}")
def atualizar_produto_parcial(
    produto_id: int,
    produto_atualizacao: ProdutoPatchSchema
):

    if produto_id not in produtos_db:
        raise HTTPException(
            status_code=404,
            detail="Produto não encontrado."
        )

    produto_atual = produtos_db[produto_id]

    if produto_atualizacao.preco is not None:

        if produto_atualizacao.preco < (
            produto_atual["preco"] * 0.5
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "O novo preço não pode ser inferior "
                    "a 50% do preço atual."
                )
            )

    dados_atualizados = produto_atualizacao.model_dump(
        exclude_unset=True
    )

    produto_atual.update(dados_atualizados)

    produtos_db[produto_id] = produto_atual

    return {
        "mensagem": "Produto atualizado com sucesso.",
        "produto": produto_atual
    }


# Soft Delete
@app.delete("/produtos/{produto_id}/soft")
def soft_delete_produto(produto_id: int):

    if produto_id not in produtos_db:
        raise HTTPException(
            status_code=404,
            detail="Produto não encontrado."
        )

    produtos_db[produto_id]["ativo"] = False

    return {
        "mensagem": (
            "O produto foi desativado com sucesso "
            "(Soft Delete)."
        )
    }


# PUT com comportamento de Upsert
@app.put("/produtos/{produto_id}")
def upsert_produto(
    produto_id: int,
    produto: ProdutoSchema,
    response: Response
):

    if produto_id in produtos_db:

        produtos_db[produto_id] = produto.model_dump()

        response.status_code = status.HTTP_200_OK

        return {
            "mensagem": "Produto atualizado.",
            "produto": produtos_db[produto_id]
        }

    else:

        produtos_db[produto_id] = produto.model_dump()

        response.status_code = status.HTTP_201_CREATED

        return {
            "mensagem": "Produto criado do zero.",
            "produto": produtos_db[produto_id]
        }


# Inicializador do servidor
if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000
    )
