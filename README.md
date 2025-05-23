# uiya-yutto

我克隆了 [yutto](https://github.com/yutto-dev/yutto) 并且在此基础上新增一些特性, 因为并不是所有特性值得合入上游分支, 但是那些特性对我来说可能是必要的, 所以我自己偷偷 release 一个分支.

起点是 yutto 的 `#497` PR. 我也会跟踪一些上游的更新, 但并不是全部.

## 变更日志

- [x] `--skip-download` 解析但不下载, 以 Logger 的形式.
- [x] 支持包含复杂 query 链接的 `ugc_vido_list` p 的解析, 防止总是下载 `p1`. (已合入上游)
- [x] `--ffmpeg-path` 支持指定 local_ffmpeg, 而并非总是使用环境变量下的 `ffmpeg`.
- [x] release v0.0.1
- [x] 重定义部分为 INFO 的 Logger 为 Custom.
- [x] release v0.0.2-pre
- [x] 支持 ugc_video 不同 p 不互相覆盖, 以 page 作为标识符, video_name 作为文件名.
- [x] release v0.0.2-pre.1
- [x] 不在 Logger 中打印 page.
- [x] release v0.0.2-pre.2



