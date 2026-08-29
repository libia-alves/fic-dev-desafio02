from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.models import Base, Documento


def test_bug008_same_filename_different_content_does_not_crash():
    """Regressão do BUG-008: nome_arquivo não pode ter unique=True, senão dois
    arquivos com o mesmo nome mas conteúdo diferente derrubam o pipeline com
    IntegrityError, violando o requisito de não interromper tudo por um único
    documento problemático. A deduplicação real é por hash_sha256."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(Documento(nome_arquivo="atendimentos.pdf", hash_sha256="a" * 64, total_paginas=1, metodo="extracao_direta"))
        session.add(Documento(nome_arquivo="atendimentos.pdf", hash_sha256="b" * 64, total_paginas=1, metodo="extracao_direta"))
        session.commit()  # não deve levantar IntegrityError
        assert session.query(Documento).count() == 2
