# 官方文档与源码观察

本文件只保留会影响实现决策的资料索引与源码归纳。需要核对 API 时，先看当前项目的 Koishi 版本和类型，再打开对应链接；网页示例可能随版本变化。

## 官方资料

- [Koishi 介绍](https://koishi.chat/zh-CN/manual/introduction.html)：框架定位、TypeScript、控制台、插件市场、单元测试与热重载。
- [官方文档仓库](https://github.com/koishijs/docs)：中文文档源文件在 `zh-CN/`，文档许可证为 CC-BY-SA-4.0；`.vitepress/` 主题部分另有 AGPL-3.0。
- [认识插件](https://github.com/koishijs/docs/blob/main/zh-CN/guide/plugin/index.md)：入口导出、嵌套插件、配置文件解析和默认导出优先级。
- [配置构型](https://github.com/koishijs/docs/blob/main/zh-CN/guide/plugin/schema.md)：`Schema<T>`、默认值、校验、控制台表单和插件元属性。
- [生命周期](https://github.com/koishijs/docs/blob/main/zh-CN/guide/plugin/lifecycle.md)：`ready`、`dispose`、`fork`、`reusable` 与上下文副作用边界。
- [服务与依赖](https://github.com/koishijs/docs/blob/main/zh-CN/guide/plugin/service.md)：`inject`、`ctx.inject`、`Service`、声明合并与 `package.json` 服务元数据。
- [指令开发](https://github.com/koishijs/docs/blob/main/zh-CN/guide/basic/command.md)：声明参数、选项、类型、别名、帮助和子指令。
- [事件系统](https://github.com/koishijs/docs/blob/main/zh-CN/guide/basic/events.md)：事件命名、类型扩充、触发方式和 dispose。
- [中间件](https://github.com/koishijs/docs/blob/main/zh-CN/guide/basic/middleware.md)：`next` 链、异步、前置和临时中间件。
- [工作区开发](https://github.com/koishijs/docs/blob/main/zh-CN/guide/develop/workspace.md)：`setup/build/clone`、`external` 目录、HMR 和依赖管理。
- [发布插件](https://github.com/koishijs/docs/blob/main/zh-CN/guide/develop/publish.md)：包名、semver、`peerDependencies`、`koishi` 字段和发布流程。

## 从 npm 包追到 GitHub 源码

用户提出“参考某个 `@koishijs/plugin-*` 插件”时，先从 npm 的包信息确认版本和 `repository` 字段，再打开该字段指向的 GitHub 仓库；不要把 npm README 或打包后的 `lib` 当作源码依据。对照仓库的 `package.json`、`src/`、`tests/`、CI 和构建配置，记录版本、入口导出、服务声明、测试命令和资源清理方式。

官方插件常见仓库不一定按 npm 包名命名：例如 `@koishijs/plugin-repeater` 这类包可位于 Koishi 组织的 monorepo 子目录。遇到仓库名不确定时，先用 npm 的 `repository` 链接或 GitHub 组织搜索结果确认，禁止凭包名猜测并据此修改代码。

## 已研究的源码模式

### `koishijs/common` 中的 repeater（npm：`koishi-plugin-repeater`）

源码：[packages/repeater/src/index.ts](https://github.com/koishijs/common/blob/main/packages/repeater/src/index.ts)。这是一个小而完整的示例仓库：每个插件在 monorepo 的 `packages/<name>/` 下独立拥有 `src/`、`tests/`、`README.md`、`package.json` 和 `tsconfig.json`。

- 用 `Schema.union([RepeatHandler, Function])` 允许声明式配置或回调策略；默认值和描述直接进入控制台表单。
- 入口 `apply(ctx, config)` 先用 `ctx.guild()` 限定作用域，再按 `session.cid` 保存状态，避免不同群共享计数。
- 用 `ctx.before('send', ...)` 更新发送状态，用 middleware 处理消息；通过 `next(text)` 保留 Koishi 的单次消息处理链。
- 通过 `ctx.bots[uid]` 忽略机器人自身消息；策略函数只负责决定是否回复，流程函数负责状态机和调度。

### `koishijs/common` 中的 schedule（npm：`koishi-plugin-schedule`）

源码：[packages/schedule/src/index.ts](https://github.com/koishijs/common/blob/main/packages/schedule/src/index.ts)。它展示了需要数据库、国际化和定时资源的插件如何组织。

- `inject = ['database']` 明确服务依赖；用 declaration merging 扩展 `Tables`，再用 `ctx.model.extend()` 声明表结构。
- 在 `ready` 时加载持久化任务，并在 bot 上线事件后补齐离线期间无法准备的任务。
- 每次定时回调前用数据库确认任务仍存在；一次性任务删除后再执行，循环任务用 `ctx.setTimeout/ctx.setInterval`，让 Koishi 能回收计时器。
- `Schema.computed()` 让配置按会话过滤器解析；`ctx.i18n.define()` + `session.text()` 处理本地化；命令用 authority、`checkUnknown`、选项和结构化错误文本表达权限与交互。

### 从官方插件集合得到的仓库级规范

官方常用插件集合仓库：[koishijs/common](https://github.com/koishijs/common)。仓库 README 明确把它作为常用插件示例仓库；插件功能按包拆分，统一 TypeScript、Schema、测试和文档。可参考 `alias`、`feedback`、`forward`、`rate-limit`、`recall`、`repeater`、`respondent`、`schedule`、`shutdown`、`spawn`、`sudo`、`verifier` 等包的相同目录和脚本约定。

这些源码共同体现的设计规范：

1. 入口只负责导出元属性、声明依赖、构造 Schema 和组合 Koishi 原语；复杂业务拆到命名函数或模块。
2. 数据模型通过 `ctx.model` 声明，持久化状态和会话运行状态分开；运行状态按 `cid/sid` 隔离。
3. 事件、中间件、命令和定时器都挂在插件上下文上；外部资源用生命周期事件成对管理。
4. 插件包的 `README` 描述用户可见行为，`package.json` 提供 Koishi 版本、服务关系、仓库和许可证信息；测试与构建脚本随包保留。
5. 通过可配置回调、`Schema.computed` 和子插件注入适配不同部署环境，避免把平台、群号、账号写死在源码里。

## 评估新源码时的检查表

- 是否从 `koishi` 导入类型/API，并遵循当前版本而非旧 `ctx` 写法？
- 入口是否有清晰的 `name/apply/Config`，服务依赖是否用 `inject` 或 `ctx.inject` 表达？
- 是否利用上下文自动回收，且手动创建的 timer、socket、server、watcher 有 dispose？
- command 是否声明参数类型和帮助，middleware 是否正确 `return/await next()`？
- 持久化数据是否有模型/迁移策略，状态是否按会话作用域隔离？
- `package.json` 是否分清运行时、类型、peer 依赖并填写 Koishi 元数据？
- 是否有能运行的 build/test，失败时是否报告真实阻塞而非只做静态检查？
# 官方 `@koishijs/plugin-*` 源码样本

以下样本来自 npm 包名对应的 GitHub 源码仓库，不以 npm 页面中的 README 或构建产物为依据。版本会变化，使用前仍需核对当前分支和本地 `koishi` 版本。

## `@koishijs/plugin-help`

源码：[koishijs/koishi/plugins/common/help](https://github.com/koishijs/koishi/tree/master/plugins/common/help)。

- 入口导出 `name`、`Config` 和 `apply(ctx, config)`；`Schema.object` 为快捷方式和选项提供默认值、描述和控制台配置。
- 用 `ctx.i18n.define()` 注册 `zh-CN/en-US` 文案，以 `session.text()` 返回本地化消息。
- 通过 `ctx.command('help [command]')`、`.option()`、`.action()` 构建指令树，监听指令生命周期并通过事件扩展帮助生成；这体现“声明式指令 + 事件扩展点”的组合模式。
- 需要数据库时使用 Koishi 的观察/收集 API，而不是自行维护全局用户缓存。

## `@koishijs/plugin-broadcast`

源码：[koishijs/koishi/plugins/common/broadcast/src/index.ts](https://github.com/koishijs/koishi/blob/master/plugins/common/broadcast/src/index.ts)。

- 导出 `inject = ['database']`；即便配置为空，也保留 `Config = Schema.object({})` 作为统一插件接口。
- `broadcast <message:text>` 配合 `authority`、`forced`、`only` 选项，把权限检查、数据库频道筛选和 Bot 广播动作分层；默认走 `ctx.broadcast`，特定频道才查询数据库并调用 `session.bot.broadcast`。
- 用 i18n 和 Koishi 的 `Channel.Flag.silent` 处理用户可见反馈与静默频道，不直接假设平台 API 的文本格式。

## `@koishijs/plugin-server`

源码：[koishijs/koishi/plugins/server](https://github.com/koishijs/koishi/tree/master/plugins/server)。

- 这是适配/重导出模式：入口只把 `@cordisjs/plugin-server` 的默认导出和类型重新导出给 Koishi 生态。
- 这种包不应复制底层服务实现；需要扩展时先判断是包装现有服务、声明服务依赖，还是编写新的 Koishi 插件。

## `@koishijs/plugin-hmr`

源码：[koishijs/koishi/plugins/hmr](https://github.com/koishijs/koishi/tree/master/plugins/hmr)。

- 通过 loader 缓存、插件依赖图和运行时子节点维护增量重载；对 pending/reloads、accepted/declined 集合和错误回滚进行隔离。
- 设计上的启示是：热重载不是简单重新 `require`，而是按插件粒度 dispose/reload，并保留依赖图的一致性；插件自身应保证副作用可逆，让 HMR 能安全接管。

## 其他源码对照

- [koishijs/common](https://github.com/koishijs/common)：`koishi-plugin-repeater` 与 `koishi-plugin-schedule` 是状态机、Schema、数据库、定时器和测试目录的简洁示例。
- [koishijs/plugins](https://github.com/koishijs/plugins)：多个独立插件子包共享 `package.json + src + tests` 结构，可观察插件包之间如何保持边界。
- [Koishi 主仓库插件目录](https://github.com/koishijs/koishi/tree/master/plugins)：官方 `@koishijs/plugin-*` 的入口与服务实现。

从这些样本归纳的模式是：入口元数据稳定、Schema 是运行时契约、Context 是可逆的资源作用域、服务通过注入形成依赖图、指令/事件/中间件负责交互、i18n 和数据库通过官方服务完成跨平台能力。避免手动全局注册、按加载顺序猜服务、把状态写到模块全局、把平台 API 绑死在命令处理器里。

## Mock 测试

官方 [Mock 插件文档](https://koishi.chat/zh-CN/plugins/develop/mock.html) 和 [测试实践](https://koishi.chat/zh-CN/cookbook/practice/testing.html) 提供离线测试路线：创建 `new Context()`，加载 `@koishijs/plugin-mock`（涉及数据库时再加载内存数据库），`app.start()` 后用 `app.mock.client(userId, channelId)` 创建客户端；用 `client.receive()`、`shouldReply()`、`shouldNotReply()` 覆盖命令和中间件，用 `mock.receive(event)` 覆盖会话事件，用 `initUser/initChannel` 设置权限和数据。异步 message 监听器、未 `await/return` 的异步 middleware/command、直接调用 Bot API 的代码需要单独测试，因为 Client 断言不一定能捕获其时序。

## 额外样本：`@koishijs/plugin-bind` 与 SQLite

- [`@koishijs/plugin-bind`](https://github.com/koishijs/koishi/blob/master/plugins/common/bind/src/index.ts) 使用 `inject = ['database']`、双语 i18n 和 `ctx.database.set('binding', ...)` 持久化绑定；一次性 token 保存在插件实例内，并用 `ctx.setTimeout` 过期清理。它展示了“持久状态 + 短期状态 + 超时回收”的安全令牌模式，令牌阶段和作用域要显式建模。
- [`@koishijs/plugin-database-sqlite` 文档](https://koishi.chat/zh-CN/plugins/database/sqlite.html) 的配置以 Schema 暴露 `path`，默认 `data/koishi.db`；数据库实现插件提供 `database` 服务，业务插件只声明 `inject` 并通过 `ctx.database` 使用。不要在业务插件中直接打开 SQLite 文件。

### `@koishijs/plugin-broadcast` 的包与测试约定

源码的包配置还体现了发布层规范：`main`/`typings` 指向 `lib`，`files` 保留 `lib` 与 `src`，`repository` 使用 monorepo 的 `directory`，`keywords` 面向 bot/chatbot/koishi/plugin，`koishi` 元数据包含 `category`、多语言 `description`、`service.required` 和 `locales`；`peerDependencies` 声明兼容的 Koishi 范围，测试依赖 `@koishijs/plugin-mock` 和内存数据库驱动。其测试用 mock client、`initUser/initChannel`、静音频道标记和 spy 验证权限、路由与 Bot API 调用。实现发布清单或测试时可参考这些字段，但必须按目标仓库当前版本调整。

## npm 检索与源码入口

本次先在 [npm `@koishijs/plugin-*` 搜索](https://www.npmjs.com/search?q=%40koishijs%2Fplugin-)确认官方包名，再转到源码仓库阅读实现，未把 npm 包详情页作为源码依据。检索结果包含 `@koishijs/plugin-http`、`@koishijs/plugin-server`、`@koishijs/plugin-database-sqlite`、`@koishijs/plugin-adapter-qq`、`@koishijs/plugin-adapter-discord`、`@koishijs/plugin-adapter-kook`、`@koishijs/plugin-console` 等；本 skill 重点采用在 [koishijs/koishi](https://github.com/koishijs/koishi/tree/master/plugins) 中可核对的 `help`、`broadcast`、`bind`、`server`、`hmr` 源码作为设计样本。包的 GitHub 路径可能随 monorepo 重组而改变，实际任务应以 npm `repository` 字段和当前仓库为准。
