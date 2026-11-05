from django.test import TestCase, Client

class PainelDashboardTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_acesso_painel_com_sessao(self):
        session = self.client.session
        session['usuario_logado'] = 'teste'
        session['perfil_usuario'] = 'Colaborador'
        session.save()

        response = self.client.get('/painel/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'inventario/index.html')

