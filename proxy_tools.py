from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.uic import loadUi

import sys
import platform
import time
from net_api import *

from threading import Thread


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()

        if not platform.system().lower() == "windowsf":
            QtWidgets.QMessageBox.warning(self, "Warning",
                                          "本工具暂时仅支持Windows系统！",
                                          QtWidgets.QMessageBox.Close)
            exit(-1)

        loadUi("proxy.ui", self)
        self.data = {}
        self.ports_used = []
        self.update_ip_list()

        self.ip_list.currentRowChanged.connect(self.update_rules_list)

        self.delete_rule.clicked.connect(self.remove_rule)
        self.reload.clicked.connect(self.reload_list)
        self.add_rule.clicked.connect(self.add_rules)

        # self.ip_list = QtWidgets.QListWidget()
        # self.rules_list = QtWidgets.QListWidget()
        self.timer1 = QtCore.QTimer()
        self.timer1.timeout.connect(self.check_input)
        self.timer1.start(100)

        self.reload_flag = False

        # self.gather_rules = QtWidgets.QCheckBox()
        self.gather_rules.clicked.connect(self.reload_list)

        # self.statusbar = QtWidgets.QStatusBar()
        # self.set
        label = QtWidgets.QLabel("感谢使用本工具！<a href='https://github.com/LSH9832'>作者GitHub主页</a>")
        label.setOpenExternalLinks(True)
        self.statusbar.addPermanentWidget(label)
        self.setWindowIcon(QtGui.QIcon("icon.ico"))

    def check_input(self):

        if self.reload_flag:
            self.reload_flag = False
            self.statusbar.showMessage("")
            self.setEnabled(True)
            time.sleep(0.1)
            self.reload_list()

        self.port_from_start.setEnabled(len(self.ip_from.text()))
        self.port_from_end.setEnabled(len(self.port_from_start.text()))
        self.port_to_start.setEnabled(len(self.port_from_start.text()))

        self.port_to_end.setText('')
        if len(self.port_from_start.text()) and len(self.port_from_end.text()) and len(self.port_to_start.text()):
            if self.port_from_start.text().isdigit() and self.port_from_end.text().isdigit() and self.port_to_start.text().isdigit():
                pte = int(self.port_to_start.text()) + int(self.port_from_end.text()) - int(self.port_from_start.text())
                self.port_to_end.setText(str(pte))




    def update_ip_list(self):

        now_index = self.ip_list.currentRow()

        self.data, self.ports_used = get_now_proxy()

        self.ip_list.clear()
        for this_ip, _ in self.data.items():
            self.ip_list.addItem(this_ip)

        if now_index < len(self.data.keys()):
            self.ip_list.setCurrentRow(now_index)


    def update_rules_list(self, index):
        # print(index)
        self.rules_list.clear()
        if index < 0:
            return
        try:
            ip = self.ip_list.item(index).text()
            rules = self.data[ip]

            tab_len = 12
            tab_num = 1

            for rule in rules:
                if len(rule) == 2:
                    port_str = f"{rule[0]}"
                    len_space = tab_len * tab_num - len(port_str)
                    port_str += "\t" * (len_space // tab_len + int(len_space % tab_len > 0))
                    self.rules_list.addItem(f"{port_str}→ {rule[1]}")
                elif len(rule) == 4:
                    if self.gather_rules.isChecked():
                        port_str = f"{rule[0]}-{rule[2]}"
                        len_space = tab_len * tab_num - len(port_str)
                        port_str += "\t" * (len_space // tab_len + int(len_space % tab_len > 0))
                        self.rules_list.addItem(f"{port_str}→ {rule[1]}-{rule[3]}")
                    else:
                        for ip_f, ip_t in zip(range(rule[0], rule[2] + 1), range(rule[1], rule[3] + 1)):
                            port_str = f"{ip_f}"
                            len_space = tab_len * tab_num - len(port_str)
                            port_str += "\t" * (len_space // tab_len + int(len_space % tab_len > 0))
                            self.rules_list.addItem(f"{port_str}→ {ip_t}")



                else:
                    raise IndexError(f"Length of this rule is not correct, expect 2 or 4, got {len(rule)}: {rule}")

        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", str(e), QtWidgets.QMessageBox.Close)

    def add_rules(self):

        # self.ip_from = QtWidgets.QLineEdit()

        try:
            assert len(self.ip_from.text()), "内网IP不能为空!"
            assert len(self.port_from_start.text()), "内网起始端口不能为空！"
            assert len(self.port_to_start.text()), "映射起始端口不能为空！"

            assert self.port_from_start.text().isdigit(), "内网起始端口必须为数字！"
            assert self.port_to_start.text().isdigit(), "映射起始端口必须为数字！"

            if len(self.port_from_end.text()):
                assert self.port_to_end.text().isdigit(), "映射结束端口必须为数字！"
                assert int(self.port_from_end.text()) > int(self.port_from_start.text()), "内网结束端口应大于内网起始端口！"

                to_start = int(self.port_to_start.text())
                warn_ports = []

                def add():
                    for index, port in enumerate(range(int(self.port_from_start.text()), int(self.port_from_end.text()) + 1)):
                        if to_start + index in self.ports_used:
                            warn_ports.append(to_start + index)
                        else:
                            print(f"now processing port {to_start + index}")

                            add_rule(self.ip_from.text(), port, to_start + index)

                    if len(warn_ports):
                        QtWidgets.QMessageBox.warning(self, "Warning",
                                                      f"{warn_ports[0]}"
                                                      f"{f'等{len(warn_ports)}个' if len(warn_ports) > 1 else ''}端口已被占用！",
                                                      QtWidgets.QMessageBox.Close)
                    self.reload_flag = True

                self.statusbar.showMessage("正在添加，请稍等")
                self.setEnabled(False)
                Thread(target=add).start()

            else:
                if int(self.port_to_start.text()) in self.ports_used:
                    QtWidgets.QMessageBox.warning(self, "Warning",
                                                  f"{self.port_to_start.text()}端口已被占用！",
                                                  QtWidgets.QMessageBox.Close)
                else:
                    add_rule(self.ip_from.text(), self.port_from_start.text(), self.port_to_start.text())

                self.reload_list()

        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", str(e), QtWidgets.QMessageBox.Close)


    def remove_rule(self):

        index = self.rules_list.currentRow()

        if index < 0:
            return

        rule_str = self.rules_list.item(index).text().split()

        ports_from = rule_str[0]
        ports_to = rule_str[-1]

        if "-" in ports_from:
            assert "-" in ports_to
            ports_to_start, ports_to_end = ports_to.split("-")
            ports_to_start, ports_to_end = int(ports_to_start), int(ports_to_end)

            self.statusbar.showMessage("正在删除，请稍等")
            self.setEnabled(False)
            def remove():
                for i in range(int(ports_to_start), int(ports_to_end) + 1):
                    print(f"now processing port {i}")
                    remove_rule(i)
                self.reload_flag = True



            Thread(target=remove).start()

        else:
            remove_rule(ports_to)

            self.reload_list()


    def reload_list(self, *args, **kwargs):
        self.update_ip_list()
        self.update_rules_list(self.ip_list.currentRow())


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


