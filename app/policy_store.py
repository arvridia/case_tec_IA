from typing import List
from pydantic import BaseModel


class PolicyChunk(BaseModel):
    id: str
    title: str
    text: str


def get_policy_chunks() -> List[PolicyChunk]:
    return [
        PolicyChunk(
            id="POL-1",
            title="Somente processos transitados em julgado e em fase de execução",
            text=(
                "A empresa só compra crédito de processos que já transitaram em julgado "
                "e estejam na fase de execução."
            ),
        ),
        PolicyChunk(
            id="POL-2",
            title="Valor de condenação informado",
            text=(
                "É obrigatório informar o valor da condenação para que o crédito possa ser analisado."
            ),
        ),
        PolicyChunk(
            id="POL-3",
            title="Valor mínimo de condenação",
            text=(
                "Se o valor da condenação for menor que R$ 1.000,00, o crédito não é comprado."
            ),
        ),
        PolicyChunk(
            id="POL-4",
            title="Processos trabalhistas não são comprados",
            text=(
                "Condenações na esfera trabalhista não são elegíveis para compra de crédito."
            ),
        ),
        PolicyChunk(
            id="POL-5",
            title="Óbito do autor sem habilitação",
            text=(
                "Se houver óbito do autor e não houver habilitação regular de sucessores no inventário, "
                "o crédito não é comprado."
            ),
        ),
        PolicyChunk(
            id="POL-6",
            title="Substabelecimento sem reserva de poderes",
            text=(
                "Se o substabelecimento for sem reserva de poderes, o crédito não é comprado."
            ),
        ),
        PolicyChunk(
            id="POL-7",
            title="Honorários",
            text=(
                "Devem ser informados honorários contratuais, periciais e sucumbenciais sempre que existirem."
            ),
        ),
        PolicyChunk(
            id="POL-8",
            title="Documentos essenciais",
            text=(
                "Se faltar documento essencial – por exemplo, comprovação do trânsito em julgado – "
                "o processo deve ser marcado como incomplete."
            ),
        ),
    ]
