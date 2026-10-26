# Clash Verge 代理策略参考

`Script.example.js` 保存 2026-10-26 当前全局扩展脚本的脱敏副本，不由默认恢复流程启用。

- 保留 VPS Hysteria2 / Reality 节点结构、订阅 provider、主策略组及 AI 服务组的整合逻辑。
- 当前脚本不再注入 `dialer-proxy` 链式连接，也不再注入原来的 AWS 和购买的 SOCKS5 节点。
- 保留代理服务器管理连接的直连规则；地址已替换为文档示例地址和域名。
- 对使用 `combined-panstar` provider 的独立配置保持直接返回，不改其节点与规则。

所有节点地址、密码、UUID、公钥、短 ID、指纹和订阅 URL 均替换为占位符。
`REPLACE_LOCALLY`、`https://example.invalid/subscription`、`192.0.2.1`、
`proxy.example.invalid` 不能直接用于连接。使用前在本地补齐自己的参数，并在
Clash Verge 中验证配置；不要将补齐后的副本或完整 profiles.yaml 上传到公开仓库。
订阅内容、独立配置内的凭据、运行状态和选中节点不在此快照中。
