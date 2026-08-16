from django.test import TestCase

from apps.servermanager.models import EmailSendLog, commands


class CommandsModelTest(TestCase):
    """servermanager.commands 模型冒烟测试。"""

    def test_create_and_str(self):
        cmd = commands.objects.create(
            title="查看监听端口",
            command="netstat -tlnp",
            describe="列出所有监听中的端口",
        )
        self.assertEqual(cmd.title, "查看监听端口")
        self.assertEqual(str(cmd), "查看监听端口")
        self.assertIsNotNone(cmd.creation_time)
        self.assertIsNotNone(cmd.last_modify_time)

    def test_persist_multiple(self):
        c1 = commands.objects.create(title="a", command="x", describe="d")
        c2 = commands.objects.create(title="b", command="y", describe="d")
        titles = list(commands.objects.values_list("title", flat=True))
        self.assertIn(c1.title, titles)
        self.assertIn(c2.title, titles)


class EmailSendLogModelTest(TestCase):
    """servermanager.EmailSendLog 模型冒烟测试。"""

    def test_create_with_success(self):
        log = EmailSendLog.objects.create(
            emailto="user@example.com",
            title="测试邮件",
            content="hello world",
            send_result=True,
        )
        self.assertTrue(log.send_result)
        self.assertEqual(str(log), "测试邮件")
        self.assertIsNotNone(log.creation_time)

    def test_default_send_result_false(self):
        log = EmailSendLog.objects.create(
            emailto="user@example.com", title="t", content="c"
        )
        self.assertFalse(log.send_result)
