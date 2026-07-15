from django.core.management.base import BaseCommand

from src.dados_comuns.models import *
from src.produto.models import *


class Command(BaseCommand):
    """
    Script feito para corrigir logs antigos (~~ Agosto 2021 para trás)
    de Homologações de Produtos. Estavam errados pois em determinado período
    foram incluídos novos status entre os status já existentes no modelo de
    class LogSolicitacoesUsuario. Novos status devem sempre ser colocados ao
    abaixo do último status.
    """

    help = "Corrige logs antigos de Homologações de Produtos"

    # flake8: noqa: C901
    def handle(self, *args, **options):
        lista_uuids_homologacoes = [
            "012685fb-ddcf-419a-b98f-8dbaec66710a",
            "016318f6-27ad-4d4b-948c-e0cbf9941e54",
            "02ddb859-ea9b-493b-aa13-8ba7150f9ae0",
            "030f847c-da12-45a5-8889-e6701388276f",
            "0365e3e2-1732-4710-9ebf-aff829833560",
            "054725be-8838-4791-a2ed-d07ce85b93b1",
            "0589390d-e773-43b2-b050-a6f13f9d5eb0",
            "060431d1-c9f1-4e33-826f-bb2947aea27d",
            "069a98e6-4b34-47c9-862c-09c8a01185c5",
            "07fa2d7b-ff15-4872-8bb3-1dd005c8833c",
            "080a4796-82dd-464b-9082-f97984d9024a",
            "0922e712-ee3b-4c1e-b1d4-4e98f20801f4",
            "0a250df6-48ab-4eb6-bf35-410e0005a411",
            "0a2fe7a6-0e63-4b98-8b79-73cb329c619f",
            "0b203a4d-0981-41c4-ba83-1f7e6553acab",
            "0b8187e6-b4c0-4ede-8b13-a5c3801b2582",
            "0ba0ffa3-23b0-405a-b0ff-8d2d1dd8ee1a",
            "0bd125c2-878e-41a3-9e0a-9f29adbd5ed1",
            "0d092b54-cca1-437b-8864-7c8910026c77",
            "0e585101-2ad2-4a12-b484-c59f6b119795",
            "0f113585-cb61-4116-8532-89e5a1d88ca3",
            "0f35268f-1f41-46bf-a26b-4c98641c3ef0",
            "0f5f3322-72bd-495e-b90c-0ffe058cba0b",
            "1410c6a4-e5c6-4ce6-b934-7d29e58a66c4",
            "1438bb3a-7cf0-4c62-8346-bc0170c170e6",
            "1480ac3f-1031-4851-8c90-87b63ea9d9ba",
            "1650e1d7-f07f-4f65-a1cd-d5f52a563a84",
            "187f2533-cf49-40fc-8365-acb4e29fbebe",
            "199e752f-8721-4bfa-9949-a831e582dbb9",
            "1af4245f-9fce-4239-a710-4f6d7042ee3c",
            "1cc7a4d9-0fb6-4e75-9264-990542d3ad61",
            "1cc80a0a-a961-4cb7-82bf-1e43b95402af",
            "1dbeebc6-bdab-4c28-88fa-b53c01ba25d8",
            "1fdd66f3-a8ba-46ac-bdfa-a8ffc7563de0",
            "204afe36-e133-4802-acd1-97cbc65587b9",
            "222b2741-efcd-4fdd-91b3-ed7653496529",
            "224111d9-c898-403d-825b-c788db6d9784",
            "24d24992-7af8-4184-ae2e-68a818017a34",
            "25210736-c04f-4e03-8e27-0683220e2e7a",
            "25555759-53fb-42b5-beb9-3ca8495cc2e2",
            "261a9404-68d7-44ac-9dc4-8a06884e348d",
            "275c0ad5-aba3-4247-acd0-2c69b3c37652",
            "290217ea-e822-4181-966b-95a56cf0ff9b",
            "29984447-156e-4ac2-ad25-46b71026d9c2",
            "2a435bd8-e6da-4c3d-950f-7365bf5c68e1",
            "2b35fa2a-4a4f-4470-b609-8b08e626b4bf",
            "2d297d53-3c80-4bef-b481-fe0f60561249",
            "2e256c14-6663-40fe-95c9-ad57303c764a",
            "2e757a7b-04ef-44f6-aa32-332419bc6946",
            "2f12e711-7ee7-4c83-b0fc-79dfb41263b0",
            "3173f0d2-0112-45a3-b5c7-cc7130a6afde",
            "31cb290c-c402-4825-aeb9-c5e2fefff311",
            "32ec081c-a7e4-46f6-b8da-663246354493",
            "330329f6-8466-4ac8-bb53-f46a8d39a468",
            "337ea549-5a6c-4803-a032-93886dceea02",
            "34f36265-9d63-4018-99cf-756adbeb8461",
            "3506dfb7-e0b0-4010-ba58-191e97d6aa6d",
            "371366b1-715a-4c29-93b3-f346c94a7427",
            "3769fcba-3399-42f1-bd2e-b062216abe03",
            "383145e8-d00e-426b-bd96-f26435246747",
            "3a069d05-aca8-432f-b235-944c1e96a1d2",
            "3a19914a-a63a-4398-9768-8bbb8e66d6d6",
            "3b67c352-0fd7-465a-88b9-1601673a43aa",
            "3c90f022-b515-46fc-ab13-6242d327dd76",
            "3cbcecd8-7462-4611-b570-b4b1376366db",
            "3d37b8b2-ea77-48c3-84af-e8f31187aa3d",
            "42a67110-2c8a-4e98-9089-18e5c5b42272",
            "43e9aab6-49b3-4907-9b88-a7c0f2f4d976",
            "45c68073-535c-4b36-b3d8-7a147d19f8b6",
            "45d8e9ee-b5f4-48bf-8304-f0eb6fd532c2",
            "463ea729-6ef0-4424-9114-2af8f5aeb5b8",
            "46fd0868-f71c-489a-8f06-b6d03182b885",
            "4856a38d-db76-47be-97df-193bf6dc5721",
            "48bd989c-14ac-47bc-a70b-9627e715dbc8",
            "48c97d3b-addb-463a-8481-29957db8eed3",
            "48d88a7f-bf38-4331-ae80-cf9ec229246c",
            "49728c57-39a2-435e-8ae5-22f54ae5635f",
            "49e2403b-40df-4c5c-a28d-89e2b13e4ff1",
            "4a3ba013-4fe0-42b2-a626-f1224c1c73a0",
            "4aa32d31-dc59-4b9b-aae0-0f6a6ca5b847",
            "4af3ce5b-7232-4e6c-b7e2-50c45230381b",
            "4bbab089-bd6f-498d-b8f1-e0718a7448de",
            "4be0175e-b7c7-43de-9a16-d8ef3dbf35c5",
            "4c3da817-a59f-4dca-b9df-32e26fe5d826",
            "4dfc7e81-52f6-428c-a85a-ed47c306cccb",
            "4e012338-1a03-41c4-8b09-1c4f0c0920c2",
            "4ec7c52b-d191-4ba1-a575-ea95743822a7",
            "4fc2a55e-6aab-43cf-bf08-4f29f47d4431",
            "51213f4a-15d7-4fc3-89b0-28d6d27431cd",
            "534504d0-030b-45f1-8beb-022cc3a3a6fc",
            "5860770f-3a7e-4ec3-91bb-9687fe35e668",
            "595d3367-23ec-44cc-87e3-12a9115bf226",
            "5ac4db4e-7b52-4ded-a467-9f95d47c0a34",
            "5b7f13c7-2597-4dab-83b2-67c7cd12312a",
            "5bb17c35-1c64-4a63-833d-40358265e393",
            "5ca765ca-2a7a-43d1-bf77-21846a920b44",
            "5e7b64ad-8e05-41b5-a863-4fc96090eae1",
            "6080f59e-1ba5-4018-8b54-4e127b8726d9",
            "609f8bf6-61e7-4b6f-abb8-f3476df157cd",
            "62824596-d4bb-4140-87a5-1f207ada1b75",
            "6287d33b-4fa3-4eb4-9639-509bde765b74",
            "6353f7e7-dba5-41ad-9895-e6fca183b41f",
            "637b10ea-7966-4dab-b779-6206b7a56d55",
            "63db753a-ecce-41f1-80d4-ecbac30e993e",
            "63f69aa7-2323-4ea3-9868-8e4017e6654a",
            "65c1bcf3-6724-4fc5-822f-4e2f96fb85bd",
            "65d7f86f-12d2-41fb-ad10-c17cf75c6c84",
            "6755c151-2592-4e81-96d7-8c71910c1d9c",
            "6832b93e-5065-436f-a965-b36db7d8378e",
            "697140fe-e9eb-43dc-b30b-2740636316f2",
            "6a63eff7-2c88-4ec7-8adb-e63be56b47b9",
            "6aca9584-615c-4e4b-9bfd-c64848a7a649",
            "6e5d3d28-bf95-4a08-b52b-2b76f7b3db4e",
            "70eaf316-aa89-41e1-bc76-54ef0a690ad4",
            "710a1e93-38d8-4a91-83f0-e68d40d2271a",
            "71271d9b-ba55-4985-8dd7-eb660843c7ef",
            "726092dd-302e-470e-909a-f94c4df247a4",
            "72be086b-7151-4316-adf5-a7790cd0a4e8",
            "72ecda3c-ceb8-4460-a4da-1be2467053f3",
            "748fbf7c-e91f-4915-9d91-68df4bb5019f",
            "767e73da-58e2-4b5f-8306-129c809d4f13",
            "7a5269f3-0cd4-4120-abd2-a5ece79b1192",
            "7b26eed3-49ed-40af-8569-15708939f166",
            "7cd1d78c-ad0f-4ddb-9269-db607dc48c89",
            "7d8e1450-a95e-4478-b948-d465043932ca",
            "7d9826d9-cdd9-4096-a8c7-7a51ee025e24",
            "7e7f096a-5ba2-4bf7-b3c7-e55c6d68755a",
            "7eda0dd9-7b10-4ac7-8417-99605229cdf9",
            "7f63924a-b479-4ec3-850b-881983f1d003",
            "8035840f-968f-4187-82ca-7ce1376c3886",
            "811b023a-692a-40bb-9344-b012d9761001",
            "8214ee17-4ddf-4ae8-a22d-dd1a4392e926",
            "8261dddb-f9b0-41ce-a0c1-b3ed8bd4853f",
            "838d808d-85a1-4e87-bd2c-c0721b457bd5",
            "83a38f8b-0cbf-410a-9cdf-1f86d3ed2f82",
            "83debccb-d59c-48f0-b88e-9b158296ab6f",
            "854d4e6c-1dc2-4d12-82a6-7293dfb2cacc",
            "858541ee-26af-4668-8e80-a9540711df65",
            "86fcca38-2742-4b99-ba18-b404f8d28e78",
            "8b244ff0-5b7c-4b3e-8b99-9ccd3f62e245",
            "8b764888-bb12-4093-a3d7-672e68617509",
            "8de61662-3105-4ff5-891b-4afc45d76fbb",
            "8e2e8bbf-b887-4ab9-b473-44589a4d31a7",
            "8ec252d0-e99b-4d42-be21-80fb04084444",
            "90ed05c6-6f97-4e73-8a16-415919dac963",
            "91aeb9a4-77c0-4b28-9569-bba2cd32533f",
            "920e2737-e334-4322-8936-81236a3025d9",
            "921246fe-7b5a-4495-b26a-b2687236c6b2",
            "95314364-b80a-4426-afaa-31aa150a36fb",
            "96390734-027b-429c-98ab-ab0000923955",
            "9703b3b5-7156-45ee-b22f-0555cbd65362",
            "98528d27-84a9-47f2-bc8f-7930fd273a90",
            "987ea8ed-e2ba-44bb-b339-3015aab6ac23",
            "9c974aca-8f97-471b-8c1d-6e972f27e2b0",
            "9d9775d4-3a92-4c7f-94e8-68e3cebe0285",
            "9f0b1d7c-f46a-43c5-a5ba-2aa527730a55",
            "9f2f99af-7de6-4962-bc9a-970e7dd4f926",
            "a15b4085-eb69-43ac-972f-5d92fefd010b",
            "a18e65c8-727f-41c9-b7ff-add5bb9775f1",
            "a46a68f8-ab31-4a63-8783-584b4d6d1f9b",
            "a6967f6d-9cde-4326-9aa8-3a776e0aea98",
            "ab9017bc-9fba-459b-a736-fa652d838a72",
            "adf181e6-250d-49f8-b57c-663313374fce",
            "af030bb4-a6ec-4ee3-abdc-740d4bd2ff02",
            "b17bf6e7-4771-402c-bdc8-4370e5ac9368",
            "b256a7d5-b5ec-4e3f-b1cd-b6836e04249d",
            "b34fc25f-2b47-489c-abdd-50a5573c41d5",
            "b3e3e846-f6b3-4574-b796-cb0ff57d5065",
            "b4184c25-1409-437f-affa-fb67c55f7914",
            "b558abea-43e1-4def-90c2-9754d9718dc6",
            "b5d66cf3-4748-47ee-8c1e-f28bd05ee11e",
            "b643d40b-3234-40a6-a601-d9abcc3b32e7",
            "b90bf0b4-e665-4e5d-8508-1e89262b7907",
            "bb208146-f977-4772-9e83-6082a325099a",
            "c22e7cc9-0786-4c41-99ad-5f1f9aadeb9a",
            "c2bffb48-a462-4382-a065-0612e867524b",
            "c2e67f73-b33f-4605-b66a-134982285fe6",
            "c4157eb3-c4b9-4377-b8ff-4cf7ccd1058b",
            "c4eb929d-de34-443e-a01b-4ae138aca078",
            "c5aa7589-69f4-4054-b063-453a5424f334",
            "c67a0dbf-a5cb-4913-baa7-fb50799dc189",
            "c7a59643-71e6-42dd-b720-f96b745a41fe",
            "c964fe98-26f7-4ced-a397-d622931fb2fc",
            "ca057740-2582-4ebd-b4b2-602cc7400df7",
            "cac668d2-f84b-4212-909a-6c2d18e39dc3",
            "cbac70cd-b5dd-407b-bf92-2d3b508ae5c4",
            "cd424cce-6a39-4bda-afe9-0e8ac3133916",
            "cf197238-36dc-40c7-b024-62a63cadfadf",
            "cf971b9b-5ce9-40ec-a61f-014688f462a0",
            "d013000e-b889-4946-9930-6760acb8e70c",
            "d0abda06-d54b-45d1-a25e-9bf2f169f8ba",
            "d0e94328-0998-4459-b0da-8ee206a9c3d4",
            "d1483237-4347-41cf-a5ee-cd6f65730b8d",
            "d1a958de-a2d1-431d-8892-627b979ba273",
            "d2f2cf47-264d-4dec-98e7-43dd81a10ded",
            "d47b3ed3-4a5b-4e9a-89cd-2a23d28beec3",
            "d7a668be-0cc6-4437-8f33-932ad82fe0a8",
            "d9afdd21-df37-4f8f-8003-a6892aea5657",
            "d9b97f68-76b8-4be1-a992-1ae907ea297b",
            "da550d1d-e1ae-4d80-948f-8878e761082f",
            "da8f0fb9-f3d5-4f51-8682-5210bde9c137",
            "dc9b4af4-2477-4bc8-8189-edde0eeed31e",
            "dcae8f09-89c5-462a-846e-79040f4b640a",
            "dd83b3df-6d3b-4f24-a472-1b1965f667c4",
            "de992d96-8b62-4e35-a678-d296a97d9cf5",
            "e0df473b-2deb-48ab-a7cb-69fdef8cf556",
            "e234462c-f21a-4844-a6b3-831293c7fe73",
            "e2aa4450-4b46-4d91-ab3c-d760cc280248",
            "e3f337c9-624c-468b-90d3-f4d27b705e21",
            "e58e7758-244e-480b-be2a-a9c8654c7b8b",
            "e6bb99df-6933-400f-8034-b83b0fc2b821",
            "e7398ec7-b4b0-45dd-9ccf-5e68b52ed608",
            "e7998df5-32a4-4b9f-ba84-20b364b81ec9",
            "e9014c22-af8f-44ec-9834-feb6989b1b10",
            "e97f70a1-682d-40b1-a148-e5d68c513c90",
            "ea52fa26-1c19-4c57-8464-e17f02532a05",
            "ebc93a76-1ba1-4045-a61e-29d6dedceb5b",
            "ed394e57-a652-4959-96a0-fc1f5a3d9a35",
            "ee3e69c1-99dd-4295-b702-3b2c3735a328",
            "ef3ffe2a-c1c7-414f-8a4e-cc895efc7383",
            "ef4a2961-684a-460b-9552-a32f977255c3",
            "f00dd679-ff3d-43ee-a6c7-893dffe7676b",
            "f1a54f65-dbab-4c9a-a63b-f58bb449506b",
            "f1c15082-cbde-4bb7-b8d3-483075c436b5",
            "f1f007c9-c244-4411-ab50-6411b91b2869",
            "f2f22e64-f20b-45cc-85f9-25302c2de6f8",
            "f33864a8-5b57-4507-b5b7-b5977b4ae46b",
            "f4745021-dee0-4436-8ec6-0e1f99a79d04",
            "f537113c-6894-4019-a894-e26900416a0c",
            "f708573c-11e1-4d00-a836-2064d7622ba1",
            "f749d968-4468-4ada-8560-5fe8ffa5698c",
            "f7a6126a-2e34-4c1e-a1b4-809dc3f8012f",
            "f7c8576b-8997-45d7-a8fc-134e75ddf437",
            "f8510493-45a8-44b6-a743-5413f128a7b1",
            "f910ff68-4865-4bfb-afa0-48b1f56c0837",
            "f9c233bb-9dbe-45c7-b32d-09b3c91acd2f",
            "fa4ca86b-8b46-4e90-b0de-373efd4f480a",
            "fa64690e-76bb-4b26-89a0-1becc043265f",
            "fb7b86d2-e32e-45be-88d5-1619f49761ad",
            "fc655601-6c60-44d8-a634-97f2ebace068",
            "fcb2c048-6bc2-4ec9-8ced-ec772513a154",
        ]

        print("")
        print("")
        print("Início...")

        _status = LogSolicitacoesUsuario.STATUS_POSSIVEIS
        status = {v: k for (k, v) in _status}

        count_de_codae_nao_homologou_para_codae_pediu_analise = 0
        count_de_homologacao_inativa_para_terc_cancelou_sol_de_homolog_prod = 0
        count_de_homologacao_inativa_para_terc_respondeu_analise = 0
        count_de_terc_resp_analise_para_terc_respondeu_analise = 0
        count_de_codae_homologou_para_questionamento_pela_codae = 0
        count_de_pendente_homolg_codae_para_codae_homologou = 0
        count_de_codae_cancelou_analise_sensorial_para_codae_suspendeu_prod = 0

        for homologacao_uuid in lista_uuids_homologacoes:
            produto_da_lista_uuids = HomologacaoDoProduto.objects.get(
                uuid=homologacao_uuid
            ).produto
            for produto in Produto.objects.all():
                if str(produto.id_externo) == str(produto_da_lista_uuids.id_externo):
                    for homologacao in produto.homologacoes.all():
                        if str(homologacao.status) != "CODAE_NAO_HOMOLOGADO":
                            for log_homolog in homologacao.logs.order_by("criado_em"):
                                if (
                                    str(log_homolog.status_evento_explicacao)
                                    == "CODAE não homologou"
                                ):
                                    count_de_codae_nao_homologou_para_codae_pediu_analise += (
                                        1
                                    )
                                    log_homolog.status_evento = status[
                                        "CODAE pediu análise sensorial"
                                    ]
                                    log_homolog.save()
                        if str(homologacao.status) == "CODAE_NAO_HOMOLOGADO" and str(
                            homologacao.uuid
                        ) in [
                            "32ec081c-a7e4-46f6-b8da-663246354493",
                            "d7a668be-0cc6-4437-8f33-932ad82fe0a8",
                            "012685fb-ddcf-419a-b98f-8dbaec66710a",
                            "b5d66cf3-4748-47ee-8c1e-f28bd05ee11e",
                        ]:
                            quant_logs = homologacao.logs.order_by("criado_em").count()
                            uuid_logs_codae_nao_homologou_para_ajustar = []
                            for log_homolog in homologacao.logs.order_by("criado_em")[
                                : quant_logs - 1
                            ]:
                                if (
                                    str(log_homolog.status_evento_explicacao)
                                    == "CODAE não homologou"
                                ):
                                    uuid_logs_codae_nao_homologou_para_ajustar.append(
                                        str(log_homolog.uuid)
                                    )
                            for log_homolog in homologacao.logs.order_by("criado_em"):
                                if (
                                    str(log_homolog.uuid)
                                    in uuid_logs_codae_nao_homologou_para_ajustar
                                ):
                                    count_de_codae_nao_homologou_para_codae_pediu_analise += (
                                        1
                                    )
                                    log_homolog.status_evento = status[
                                        "CODAE pediu análise sensorial"
                                    ]
                                    log_homolog.save()
                        if (
                            str(homologacao.uuid)
                            == "e3e29f26-f190-4365-893e-6ca3df31e9cc"
                        ):
                            for log_homolog in homologacao.logs.order_by("criado_em"):
                                if (
                                    str(log_homolog.status_evento_explicacao)
                                    == "Homologação inativa"
                                ):
                                    count_de_homologacao_inativa_para_terc_cancelou_sol_de_homolog_prod += (
                                        1
                                    )
                                    log_homolog.status_evento = status[
                                        "Terceirizada cancelou solicitação de homologação de produto"
                                    ]
                                    log_homolog.save()
                        for log_homolog in homologacao.logs.order_by("criado_em"):
                            if (
                                str(log_homolog.status_evento_explicacao)
                                == "Homologação inativa"
                                and str(homologacao.status)
                                != "TERCEIRIZADA_CANCELOU_SOLICITACAO_HOMOLOGACAO"
                            ):
                                count_de_homologacao_inativa_para_terc_respondeu_analise += (
                                    1
                                )
                                log_homolog.status_evento = status[
                                    "Terceirizada respondeu a análise"
                                ]
                                log_homolog.save()
                            if (
                                str(log_homolog.status_evento_explicacao)
                                == "Terceirizada respondeu a reclamação"
                            ):
                                count_de_terc_resp_analise_para_terc_respondeu_analise += (
                                    1
                                )
                                log_homolog.status_evento = status[
                                    "Terceirizada respondeu a análise"
                                ]
                                log_homolog.save()
                            if (
                                str(log_homolog.status_evento_explicacao)
                                == "Pendente homologação da CODAE"
                            ):
                                count_de_pendente_homolg_codae_para_codae_homologou += 1
                                log_homolog.status_evento = status["CODAE homologou"]
                                log_homolog.save()
                        if (
                            str(homologacao.uuid)
                            == "72ecda3c-ceb8-4460-a4da-1be2467053f3"
                        ):
                            for log_homolog in homologacao.logs.order_by("criado_em"):
                                if (
                                    str(log_homolog.status_evento_explicacao)
                                    == "CODAE homologou"
                                ):
                                    count_de_codae_homologou_para_questionamento_pela_codae += (
                                        1
                                    )
                                    log_homolog.status_evento = status[
                                        "Questionamento pela CODAE"
                                    ]
                                    log_homolog.save()
                        if (
                            str(homologacao.uuid)
                            == "48d88a7f-bf38-4331-ae80-cf9ec229246c"
                        ):
                            for log_homolog in homologacao.logs.order_by("criado_em"):
                                if (
                                    str(log_homolog.status_evento_explicacao)
                                    == "CODAE cancelou análise sensorial"
                                ):
                                    count_de_codae_cancelou_analise_sensorial_para_codae_suspendeu_prod += (
                                        1
                                    )
                                    log_homolog.status_evento = status[
                                        "CODAE suspendeu o produto"
                                    ]
                                    log_homolog.save()

        print("")
        print("")
        print("")
        print(
            f'Quantidade de alterações de "CODAE não homologou" para "CODAE pediu análise sensorial": --> {count_de_codae_nao_homologou_para_codae_pediu_analise}'
        )
        print("")
        print("")
        print(
            f'Quantidade de alterações de "Homologação inativa" para "Terceirizada cancelou solicitação de homologação de produto": --> {count_de_homologacao_inativa_para_terc_cancelou_sol_de_homolog_prod}'
        )
        print("")
        print("")
        print(
            f'Quantidade de alterações de "Homologação inativa" para "Terceirizada respondeu a análise": --> {count_de_homologacao_inativa_para_terc_respondeu_analise}'
        )
        print("")
        print("")
        print(
            f'Quantidade de alterações de "Terceirizada respondeu a reclamação" para "Terceirizada respondeu a análise": --> {count_de_terc_resp_analise_para_terc_respondeu_analise}'
        )
        print("")
        print("")
        print(
            f'Quantidade de alterações de "CODAE homologou" para "Questionamento pela CODAE": --> {count_de_codae_homologou_para_questionamento_pela_codae}'
        )
        print("")
        print("")
        print(
            f'Quantidade de alterações de "Pendente homologação da CODAE" para "CODAE homologou": --> {count_de_pendente_homolg_codae_para_codae_homologou}'
        )
        print("")
        print("")
        print(
            f'Quantidade de alterações de "CODAE cancelou análise sensorial" para "CODAE suspendeu o produto": --> {count_de_codae_cancelou_analise_sensorial_para_codae_suspendeu_prod}'
        )

        print("")
        print("")
        print("")
        print("Fim...")
        print("")
        print("")
