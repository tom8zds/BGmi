import xmlrpc.client
from typing import cast

from bgmi import config
from bgmi.plugin.download import BaseDownloadService, DownloadStatus
from bgmi.utils import print_error, print_warning


class Aria2DownloadRPC(BaseDownloadService):
    def __init__(self):
        self.server = xmlrpc.client.ServerProxy(config.ARIA2_RPC_URL)
        if config.ARIA2_RPC_TOKEN.startswith("token:"):
            self.token = config.ARIA2_RPC_TOKEN
        else:
            self.token = "token:" + config.ARIA2_RPC_TOKEN

        s = xmlrpc.client.ServerProxy(config.ARIA2_RPC_URL)
        r = s.aria2.getVersion(config.ARIA2_RPC_TOKEN)
        version = r["version"]
        if version:
            old_version = [int(x) for x in version.split(".")] < [1, 18, 4]
            if old_version:
                print_error("you are using old aria2 version, please upgrade to it >1.18.4")
        else:
            print_warning("Get aria2c version failed")

    def add_download(self, url: str, save_path: str) -> str:
        args = [[url], {"dir": save_path}]
        r =  self.server.aria2.addUri(self.token, *args)
        print(r)
        return cast(str,r)

    @staticmethod
    def check_dep():
        pass

    @staticmethod
    def check_config() -> None:
        if not config.ARIA2_RPC_URL.endswith("/rpc"):
            print_warning("make sure you are using xml-rpc endpoint of aria2")
        if not config.ARIA2_RPC_TOKEN.startswith("token:"):
            print_warning("rpc token should starts with `token:`")

    def get_status(self, id: str) -> DownloadStatus:
        args = (id, ["status","followedBy", "completedLength", "totalLength"])
        r = self.server.aria2.tellStatus(self.token, *args)
        print(r)
        if("followedBy" in r.keys()):
            follow = r["followedBy"][0]
            print(follow)
            return self.get_status(follow)
        active_state = DownloadStatus.downloading
        if(r["completedLength"] == r["totalLength"]):
            active_state = DownloadStatus.done
        return {
            "active": active_state,
            "waiting": DownloadStatus.downloading,
            "paused": DownloadStatus.not_downloading,
            "error": DownloadStatus.error,
            "complete": DownloadStatus.done,
        }.get(r["status"], DownloadStatus.error)
