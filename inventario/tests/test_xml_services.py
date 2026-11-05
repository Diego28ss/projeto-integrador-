from contextlib import redirect_stdout
from io import BytesIO, StringIO

from django.test import TestCase

from inventario.models.produtos.produto_models import Produtos
from inventario.services.estoque.xml_services import processar_upload_xml


def criar_xml_nfe(itens):
    itens_xml = "".join(
        (
            "<det><prod>"
            f"<cProd>{item['codigo']}</cProd>"
            f"<cEAN>{item.get('ean', 'SEM GTIN')}</cEAN>"
            f"<xProd>{item['descricao']}</xProd>"
            f"<qCom>{item.get('quantidade', '1.0000')}</qCom>"
            "</prod></det>"
        )
        for item in itens
    )
    return (
        "<nfeProc><NFe><infNFe Id=\"NFe123456\">"
        "<ide><nNF>321</nNF></ide>"
        "<emit><xNome>Fornecedor teste</xNome></emit>"
        "<total><ICMSTot><vNF>123.45</vNF></ICMSTot></total>"
        f"{itens_xml}"
        "</infNFe></NFe></nfeProc>"
    ).encode()


class ProcessarUploadXmlTests(TestCase):
    def processar(self, conteudo):
        arquivo = BytesIO(conteudo)
        with redirect_stdout(StringIO()):
            return processar_upload_xml(arquivo)

    def test_processa_nota_com_um_item_e_vincula_codigo_fornecedor(self):
        produto = Produtos.objects.create(
            nome="Tinta cadastrada",
            cod_fornecedor="FORN-1",
        )
        resultado = self.processar(
            criar_xml_nfe(
                [{"codigo": "FORN-1", "descricao": "Tinta do XML"}]
            )
        )

        self.assertEqual(resultado["chave"], "123456")
        self.assertEqual(resultado["numero"], "321")
        self.assertEqual(resultado["fornecedor"], "Fornecedor teste")
        self.assertEqual(resultado["total"], 123.45)
        self.assertEqual(len(resultado["itens"]), 1)
        self.assertEqual(
            resultado["itens"][0]["produto_vinculado_id"],
            produto.id,
        )
        self.assertEqual(resultado["itens"][0]["status_vinculo"], "sucesso")

    def test_vincula_por_codigo_de_barras_ou_codigo_interno(self):
        produto_ean = Produtos.objects.create(
            nome="Tinta pelo EAN",
            cod_barras="789123",
        )
        produto_interno = Produtos.objects.create(
            nome="Tinta pelo código interno",
            cod_interno="INTERNO-2",
        )

        resultado = self.processar(
            criar_xml_nfe(
                [
                    {
                        "codigo": "FORN-NAO-CADASTRADO",
                        "ean": "789123",
                        "descricao": "Item pelo EAN",
                    },
                    {
                        "codigo": "INTERNO-2",
                        "descricao": "Item pelo código interno",
                    },
                ]
            )
        )

        self.assertEqual(
            resultado["itens"][0]["produto_vinculado_id"],
            produto_ean.id,
        )
        self.assertEqual(
            resultado["itens"][1]["produto_vinculado_id"],
            produto_interno.id,
        )

    def test_item_sem_correspondencia_fica_pendente_e_sem_gtin_vira_vazio(self):
        resultado = self.processar(
            criar_xml_nfe(
                [{"codigo": "DESCONHECIDO", "descricao": "Item novo"}]
            )
        )

        item = resultado["itens"][0]
        self.assertEqual(item["status_vinculo"], "pendente")
        self.assertIsNone(item["produto_vinculado_id"])
        self.assertEqual(item["cEAN"], "")

    def test_rejeita_xml_que_nao_contem_estrutura_de_nfe_autorizada(self):
        with self.assertRaisesRegex(ValueError, "XML de NF-e válido"):
            self.processar(b"<documento><conteudo>invalido</conteudo></documento>")
