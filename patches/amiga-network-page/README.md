# Amiga Network page patches (temporary)

These are the submodule commits for the Amiga `config-nio` Network page and
Wi-Fi join work. They live here only because the session that wrote them could
not push to the `benjamink` forks of the submodule repositories. Apply them,
push the submodule branches, bump the submodule pointers, then delete this
directory.

| Repository | Patch | Base commit (workspace pin) |
| --- | --- | --- |
| `repos/fujinet-nio` | `fujinet-nio/0001-*.patch`: Wi-Fi `GET_ADAPTER_INFO` (0x05), station MAC + firmware version | `c75d54e` |
| `repos/fujinet-nio-lib` | `fujinet-nio-lib/0001-*.patch`: `fn_wifi_get_adapter_info()` | `fe8da17` |
| `repos/nio-config` | `nio-config/0001-*.patch`: Amiga Network page, Join picker, `wifi` SCRIPT commands | `b74c701` |

```sh
for r in fujinet-nio fujinet-nio-lib nio-config; do
  git -C repos/$r checkout -b amiga-network-page
  git -C repos/$r am "$PWD"/patches/amiga-network-page/$r/*.patch
done
```

Apply `fujinet-nio-lib` before building `nio-config`; the firmware patch is
needed only for the MAC and firmware rows (older firmware shows
"Needs newer firmware").
