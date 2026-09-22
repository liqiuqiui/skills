---
name: koishi-plugin-development
description: 创建、修改、迁移、调试、测试或发布 Koishi（尤其是 TypeScript / v4）插件时使用；涵盖插件入口、Schema 配置、指令、事件、中间件、服务依赖、控制台扩展、工作区构建与 npm 发布。不要用于只使用 Koishi 的机器人配置或与插件无关的 Node.js 项目。
---

# Koishi 插件开发

用本 skill 开发 Koishi 插件时，以用户当前项目的 `package.json`、锁文件、模板脚本和实际安装的 `koishi` 类型为准；官方文档和本 skill 中的示例用于定位 API，不能替代本地源码。Koishi 是跨平台、可扩展的 TypeScript 聊天机器人框架，插件上下文同时承担副作用隔离、服务访问和模块化加载的边界。

## 先确认版本与工作区

1. 检查当前目录、`package.json`、`koishi.yml`、`external/` 或 `plugins/`，确认这是 Koishi 应用、插件工作区还是独立插件包。
2. 查看 `koishi`、`@koishijs/*` 的实际版本和导出类型；不要把 v3、v4 或旧博客的写法混用。优先使用 TypeScript。
3. 若没有现成工作区，使用项目已有脚本；官方模板通常是 `npm init koishi@latest`，在应用目录用 `npm run setup [name]` 创建插件。创建前先确认包名是否冲突。
4. 若任务涉及具体 API 或运行错误，先在本地依赖和同仓库插件中搜索定义，再参考 [references/official-and-source-patterns.md](references/official-and-source-patterns.md) 的官方链接与源码观察。

## 选择插件形态

插件入口可导出：

- 函数 `apply(ctx, config)`，通常同时导出 `name`、`Config`、`usage` 等元属性；
- 默认导出类，构造函数接收 `ctx, config`，类或 namespace 提供 `Config`；
- 对象 `{ name, apply, ... }`。

默认导出优先于导出整体。复杂功能拆为多个子插件，在入口中用 `ctx.plugin()` 组合；每个子插件获得独立热重载和副作用边界。不要把所有逻辑塞进一个巨型 `apply`。

一个最小的 TypeScript 入口应接近：

```ts
import { Context, Schema } from 'koishi'

export const name = 'example'
export interface Config { prefix?: string }
export const Config: Schema<Config> = Schema.object({
  prefix: Schema.string().default('!').description('指令前缀。'),
})

export function apply(ctx: Context, config: Config) {
  ctx.command('hello <name:text>', '发送问候')
    .action((_, name) => `${config.prefix} ${name}`)
}
```

## 配置、依赖与生命周期

- 用 `Schema<T>` 描述配置：`Schema.object`、`array`、`dict`、`union`、`intersect`，并用 `default`、`required`、`min/max/step`、`role`、`description` 等链式元数据。Schema 同时提供校验、默认值和控制台表单；不要只写 TypeScript interface 而省略运行时 Schema。
- 插件整体依赖服务时导出 `inject = ['database']`，或用 `{ required: [...], optional: [...] }`。部分能力依赖服务时使用 `ctx.inject(['console'], subctx => ...)`，回调里使用参数 `subctx`，不要误用外层 `ctx`，否则服务热重载时容易留下副作用。
- 使用必需服务前不要通过 `if (ctx.database)` 轮询代替依赖声明：声明后 Koishi 会在服务可用时加载、服务变化时回滚并重新加载。可选服务才在运行时判断。
- 异步初始化和依赖其他插件的逻辑放在 `ctx.on('ready', ...)`；外部服务器、定时器、文件监听、第三方事件等不由 `ctx` 自动回收的副作用必须在 `ctx.on('dispose', ...)` 中清理。`ctx.plugin()` 返回的 Fork 可用 `fork.dispose()` 停用。
- 默认插件重复加载只执行一次；确实需要多实例时导出 `reusable = true`，需要跨实例共享计数或缓存时用 `fork` 事件维护实例计数，并在对应 `dispose` 中减少。
- 自定义服务继承 `Service`，通过 TypeScript declaration merging 扩展 `Context`；实现 `start/stop/fork`，并在 `package.json` 的 `koishi.service` 中声明 `required`、`optional`、`implements`。

## 编写交互逻辑

- **指令**：使用 `ctx.command('foo <required> [optional]')`；`<x:text>` 吸收剩余文本，`[...rest]` 收集变长参数。用 `.option(name, decl, { fallback, value, type, hidden })` 定义选项，用 `.alias()`、`.usage()`、`.example()` 补充帮助，用 `foo/bar` 或 `foo.bar` 注册子指令。动作回调第一个参数是 `Argv`，后面才是声明的参数。
- **事件**：一般事件用 `ctx.on/once/off`，注册会返回 dispose 函数；自定义事件先用 `declare module 'koishi' { interface Events { ... } }` 扩充类型。事件名使用小写 `param-case`，用 `feature/name` 命名空间避免冲突，时序成对事件使用 `before-feature`。
- **中间件**：消息处理优先用 `ctx.middleware((session, next) => ...)`，需要放在最前面时传第二个参数 `true`。只有截获消息时返回回复，否则必须 `return next()`；异步中间件必须 `await` 或 `return next()`，否则会出现时序错误。需要低优先级的临时回复可用 `next(callback)`。
- **上下文过滤**：用 `ctx.user/guild/channel/platform` 及 `intersect/union/exclude` 构造上下文；账号、群号、平台等部署差异写进配置或 `$filter`，不要硬编码在源码中。没有会话作用域的插件可导出 `filter = false`。
- **消息与国际化**：优先使用 `session.send()`、`session.prompt()`、`session.execute()` 等会话 API；多语言插件使用 `ctx.i18n.define()` 和 `session.text()`，不要拼接平台专属格式来代替 Koishi 元素。

## 工程规范、验证与发布

- 采用 `src/index.ts`（或仓库约定的入口）、`tests/`、`README.md`、`package.json` 的结构；源码按职责拆分，类型接口和 Schema 靠近入口，复杂服务/控制台扩展独立模块。
- 依赖分清：运行时导入放 `dependencies`；只导入类型的服务包通常放 `devDependencies`；运行时继承或调用服务包导出的类/值时，同时声明 `peerDependencies` 和 `devDependencies`。在 `package.json` 的 `koishi.service` 记录服务关系。
- 开发时运行仓库已有的 `npm run dev` / `yarn dev`（通常启用 HMR）；生产前运行 `npm run build`，再执行仓库已有的测试脚本（如 `npm test`、Vitest 或 Jest）。测试重点是命令参数和选项、middleware 的 `next` 分支、ready/dispose 清理、服务缺失/重载和配置 Schema 校验。
- 发布前只修改插件目录下的 `package.json`：包名通常是 `koishi-plugin-*`、`@scope/koishi-plugin-*` 或官方的 `@koishijs/plugin-*`；版本使用 semver；`peerDependencies` 必须包含 `koishi`；不能设置 `private: true`。补充 `repository`、`homepage`、`keywords`、贡献者和 `koishi.description/service` 元数据，构建后用 `npm run pub` 或项目约定的发布命令。
- 先做最小验证：TypeScript 编译/构建、导入插件并检查入口和 Schema、运行现有测试；若缺依赖或没有可运行的 Koishi 应用，明确报告未完成的运行验证，不要声称“已加载成功”。

## 设计模式与反模式

- **上下文组合**：让 `ctx` 创建指令、事件、中间件、子插件；通过上下文自动回收副作用，避免全局单例和手动维护监听器数组。
- **服务/依赖注入**：用 `inject` 表达服务图，用 `ctx.inject` 表达可选功能子模块；不要在插件加载阶段猜测服务是否存在。
- **状态机与作用域状态**：按 `session.cid`、`sid` 等会话边界保存状态；需要持久化时使用数据库模型，不要把群聊状态放进全局变量。复杂定时任务要记录数据库实体，并在回调执行前重新确认实体仍存在。
- **可组合策略**：把重复、反馈、权限、格式化等行为抽成回调/策略配置，通过 Schema 的 `Function` 或联合类型注入；核心流程只负责编排。
- **资源对称性**：每次 `ready/start` 建立的连接、定时器和监听器都必须有 `dispose/stop` 对应清理；不要在 `setInterval`、HTTP server、文件 watcher 中留下孤儿资源。

按需阅读参考：[references/official-and-source-patterns.md](references/official-and-source-patterns.md)。
