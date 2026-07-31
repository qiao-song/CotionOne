# Tbao — 全栈仿淘宝电商平台

## 项目概述

Tbao 是一个全栈电商交易平台，支持用户注册登录、商品发布管理、购物车、下单交易、订单物流、商品评价等完整业务闭环。前后端分离架构，Docker Compose 一键部署。

- **项目路径**: `d:/project/cloud/p20/Tbao/`
- **开发环境**: Windows 11, Git Bash, Python 3.14, Node 20, MySQL 8.0
- **本地端口**: 前端 `:3000` (Vite), 后端 `:5000` (Flask), MySQL `:3306`
- **Docker 端口**: Nginx `:8080`, Backend `:5001`, MySQL `:3308`

---

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | Vue 3 (Composition API + `<script setup>`) | SPA |
| 状态管理 | Pinia (function-based `defineStore`) | auth, goods, cart |
| 路由 | Vue Router 4 (history mode) | 导航守卫 + 路由元信息 |
| HTTP | Axios (`withCredentials: true`) | 统一拦截 401 跳转登录 |
| UI | 纯 CSS (CSS Variables 设计令牌) | 无 UI 框架依赖 |
| 图表 | 内联 SVG (价格走势图) | 无图表库依赖 |
| 后端 | Flask (应用工厂模式) | Blueprint 模块化 |
| ORM | SQLAlchemy + Flask-Migrate | 自动建表 + 手动迁移 |
| 校验 | Marshmallow Schema | 所有 POST/PUT 强制校验 |
| 认证 | PyJWT (HS256, HttpOnly Cookie) | 7 天过期, SameSite=Lax |
| 密码 | bcrypt | 哈希存储 |
| 数据库 | MySQL 8.0 (utf8mb4) | 软删除模式 |
| 部署 | Docker Compose (3 容器) | mysql + gunicorn + nginx |
| 构建 | Vite 5 | 多阶段 Docker 构建 |

---

## 项目结构

```
Tbao/
├── docker-compose.yml          # 3 容器编排 (mysql, backend, nginx)
├── init.sql                    # DDL 建表脚本 (Docker 入口)
├── CLAUDE.md                   # 本文件
├── nginx/
│   └── default.conf            # 反向代理: /api/→backend, /uploads/→文件, /→SPA
├── backend/
│   ├── Dockerfile              # python:3.10-slim + gunicorn
│   ├── requirements.txt        # Flask, SQLAlchemy, PyJWT, bcrypt, marshmallow...
│   ├── app.py                  # 应用工厂 create_app(), 自动建库, 迁移, 蓝图注册
│   ├── config.py               # 环境变量驱动配置 (DB, JWT, 上传限制)
│   ├── models/
│   │   ├── __init__.py         # db, migrate 实例 + 导入所有模型
│   │   ├── user.py             # User 模型 (含 balance)
│   │   ├── goods.py            # Goods 模型 (软删除, JSON images)
│   │   ├── order.py            # Order 模型 (物流 JSON)
│   │   └── review.py           # Review 模型 (评分 1-5)
│   ├── schemas/
│   │   ├── auth.py             # SendCodeSchema, RegisterSchema, LoginSchema
│   │   ├── goods.py            # GoodsCreateSchema, GoodsUpdateSchema
│   │   ├── user.py             # ChangePasswordSchema
│   │   ├── order.py            # CheckoutSchema, OrderStatusSchema
│   │   └── review.py           # ReviewCreateSchema
│   ├── controllers/
│   │   ├── auth.py             # /api/auth/* (send-code, register, login, me, logout)
│   │   ├── goods.py            # /api/goods/* (CRUD, toggle status, detail)
│   │   ├── user.py             # /api/user/* (my goods, profile, password, balance)
│   │   ├── order.py            # /api/orders/* (checkout, list, detail, status)
│   │   └── review.py           # /api/reviews/* (create, list by goods)
│   └── utils/
│       ├── auth.py             # JWT 生成/解码, Cookie 设置/清除, login_required 装饰器
│       ├── response.py         # success(data, msg) / fail(msg, code) 统一响应
│       └── upload.py           # UUID 重命名文件保存 (avatars/ goods/)
├── frontend/
│   ├── Dockerfile              # 多阶段: Node 20 build → nginx alpine serve
│   ├── package.json            # Vue 3, Pinia, Vue Router, Axios, dayjs
│   ├── vite.config.js          # 代理 /api 和 /uploads 到 :5000
│   └── src/
│       ├── main.js             # createApp, Pinia, Router, global.css
│       ├── App.vue             # Toast 全局提供 + <router-view />
│       ├── composables/
│       │   └── useToast.js     # inject('toast') 封装
│       ├── api/
│       │   ├── index.js        # Axios 实例 (withCredentials, 401 拦截)
│       │   ├── auth.js         # sendCode, register, login, getMe, logout
│       │   ├── goods.js        # getGoodsList, createGoods, updateGoods, deleteGoods, toggleGoodsStatus, getGoodsDetail
│       │   ├── user.js         # getMyGoods, updateProfile, changePassword, getBalance
│       │   ├── order.js        # createOrder, getOrders, getOrderDetail, updateOrderStatus
│       │   └── review.js       # createReview, getGoodsReviews
│       ├── stores/
│       │   ├── auth.js         # user, isLoggedIn, fetchUser, login, register, logout
│       │   ├── goods.js        # items, total, fetchGoods (分页)
│       │   └── cart.js         # 购物车 (localStorage 持久化, 选中/结算)
│       ├── router/
│       │   └── index.js        # 路由表 + beforeEach 导航守卫
│       ├── components/
│       │   ├── NavBar.vue      # 顶部导航 (Logo, 商品广场, 我的店铺, 购物车, 我的订单, 个人中心)
│       │   ├── GoodsCard.vue   # 商品卡片 (图片, 标题, 价格, 卖家, 购买按钮)
│       │   ├── GoodsForm.vue   # 商品发布/编辑弹窗 (多图上传, 5MB 限制)
│       │   └── Toast.vue       # 全局通知组件 (success/error/info)
│       ├── views/
│       │   ├── Layout.vue      # 布局壳 (NavBar + <router-view />)
│       │   ├── Home.vue        # 商品广场 (网格, 加载更多)
│       │   ├── Login.vue       # 登录 (密码 + 短信验证码双模式)
│       │   ├── Register.vue    # 注册
│       │   ├── Profile.vue     # 个人中心 (头像上传, 修改密码, 余额/消费统计)
│       │   ├── MyShop.vue      # 我的店铺 (商品管理: 上架/下架/编辑/删除)
│       │   ├── Cart.vue        # 购物车 (全选, 数量调整, 结算扣余额)
│       │   ├── MyOrders.vue    # 我的订单 (状态, 物流时间线, 确认收货/退货, 评价)
│       │   └── ProductDetail.vue # 商品详情 (图集, 销量/评价统计, SVG价格走势, 评价列表)
│       └── styles/
│           └── global.css      # CSS 变量, 重置, 按钮, 卡片, Toast, Modal 动画
└── uploads/                    # 运行时创建, 挂载卷
    ├── avatars/
    └── goods/
```

---

## 数据库设计

### users 表
| 列 | 类型 | 说明 |
|----|------|------|
| id | BIGINT PK | 自增主键 |
| username | VARCHAR(50) UNIQUE | 用户名 |
| phone | VARCHAR(20) UNIQUE | 手机号 |
| password_hash | VARCHAR(255) | bcrypt 哈希 |
| avatar | VARCHAR(500) | 头像 URL, 默认 `/static/default.png` |
| balance | DECIMAL(10,2) | 账户余额, 默认 10000.00 |
| created_at | DATETIME | 注册时间 |
| updated_at | DATETIME | 自动更新 |

### goods 表
| 列 | 类型 | 说明 |
|----|------|------|
| id | BIGINT PK | 自增主键 |
| title | VARCHAR(200) | 商品标题 |
| price | DECIMAL(10,2) | 价格 |
| description | TEXT | 描述 |
| images | JSON | 图片 URL 数组 |
| status | TINYINT | 1=上架, 0=下架 |
| seller_id | BIGINT FK | 卖家 ID → users.id |
| created_at | DATETIME | 发布时间 |
| updated_at | DATETIME | 自动更新 |
| deleted_at | DATETIME | 软删除时间戳 |

### orders 表
| 列 | 类型 | 说明 |
|----|------|------|
| id | BIGINT PK | 自增主键 |
| buyer_id | BIGINT FK | 买家 ID → users.id |
| goods_id | BIGINT FK | 商品 ID → goods.id |
| goods_title | VARCHAR(200) | 商品标题快照 |
| goods_price | DECIMAL(10,2) | 成交价快照 |
| goods_image | VARCHAR(500) | 商品图片快照 |
| quantity | INT | 数量, 默认 1 |
| total_amount | DECIMAL(10,2) | 总金额 |
| status | VARCHAR(20) | pending/shipped/received/returned |
| logistics | JSON | 物流记录数组 `[{time, status, location, desc}]` |
| created_at | DATETIME | 下单时间 |
| updated_at | DATETIME | 自动更新 |

### reviews 表
| 列 | 类型 | 说明 |
|----|------|------|
| id | BIGINT PK | 自增主键 |
| user_id | BIGINT FK | 评论者 → users.id |
| goods_id | BIGINT FK | 商品 → goods.id |
| order_id | BIGINT FK UNIQUE | 订单 → orders.id (一单一评) |
| rating | TINYINT | 评分 1-5 |
| content | TEXT | 评论内容 |
| created_at | DATETIME | 评论时间 |

---

## API 接口 (22 个端点, 统一 `{code, data, msg}` 格式)

### 公开接口
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/auth/send-code | 发送短信验证码 (控制台输出, 5分钟有效) |
| POST | /api/auth/register | 注册 (自动登录, 初始余额 10000) |
| POST | /api/auth/login | 登录 (用户名+密码 / 手机+密码 / 手机+验证码) |
| GET | /api/goods | 商品列表 (分页, 只显示上架+未删除) |
| GET | /api/goods/:id | 商品详情 (含销量/评价统计/价格走势) |
| GET | /api/reviews/goods/:id | 商品评价列表 (分页) |
| GET | /api/health | 健康检查 |

### 需登录接口 (JWT HttpOnly Cookie)
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/auth/me | 当前用户信息 (含余额) |
| POST | /api/auth/logout | 退出 (清除 Cookie) |
| POST | /api/goods | 发布商品 (multipart, 最多 9 张图) |
| PUT | /api/goods/:id | 编辑商品 (卖家本人) |
| DELETE | /api/goods/:id | 软删除商品 (卖家本人) |
| PUT | /api/goods/:id/status | 上架/下架切换 (卖家本人) |
| GET | /api/user/goods | 我的商品列表 |
| PUT | /api/user/profile | 更新个人资料 (头像 + 用户名) |
| PUT | /api/user/password | 修改密码 (需旧密码验证) |
| GET | /api/user/balance | 余额 + 累计消费 + 订单数 |
| POST | /api/orders | 下单结算 (扣余额, 生成物流) |
| GET | /api/orders | 我的订单列表 |
| GET | /api/orders/:id | 订单详情 (含评价状态) |
| PUT | /api/orders/:id/status | 确认收货 / 申请退货 (退货退款) |
| POST | /api/reviews | 发表评价 (需已签收订单) |

---

## 核心架构模式

### 认证流程
1. 登录/注册成功 → 后端生成 JWT → 设置 HttpOnly Cookie (`tbao_token`, 7天)
2. `login_required` 装饰器读取 Cookie → 解码 JWT → 设置 `g.user_id`
3. Axios 拦截器: 401 → 跳转 `/login?redirect=<当前路径>`
4. Vue Router beforeEach: `requiresAuth` 路由 → 检查 `authStore.isLoggedIn` → 否则跳转登录

### 文件上传
- UUID 重命名 (`uuid.uuid4().hex.ext`)
- 图片格式: jpg/png/webp, 前端限制 5MB/张, 后端限制 10MB/请求体
- 头像 → `uploads/avatars/`, 商品图 → `uploads/goods/`
- 返回相对路径 `/uploads/{subfolder}/{uuid}.{ext}`
- Nginx 直接 serve `/uploads/` (Docker) / Vite 代理 (开发)

### 软删除
- Goods 使用 `deleted_at` 时间戳
- 所有查询过滤 `deleted_at IS NULL`
- 删除仅设置时间戳, 不物理删除

### 订单交易流
1. 购物车结算 → `POST /api/orders` 提交 `{items: [{goods_id, quantity}]}`
2. 后端校验: 商品存在/上架/非本人 → 计算总额 → 检查余额
3. 扣买家余额 → 加卖家余额 → 创建订单 (status=pending) → 生成模拟物流
4. 买家可确认收货 (received) 或退货 (returned, 退款)
5. 收货后可发表评价 (一单一评, 1-5 星)

### Toast 通知
- 全局 provide/inject 模式: `App.vue` provide → 任意组件 `useToast()`
- 类型: success (绿), error (红, 4秒), info (蓝, 3秒)
- API 错误自动 toast, 字段级校验保留行内提示

### 购物车
- Pinia store + localStorage 持久化 (`tbao_cart` key)
- 存储结构: `[{goods_id, title, price, image, quantity, selected, seller_id, seller_name}]`

---

## 设计令牌 (CSS Variables)

```css
--primary: #F97316;        /* 橙色主色 */
--primary-light: rgba(249,115,22,0.1);
--primary-dark: #EA580C;
--accent: #22C55E;         /* 绿色 (价格) */
--accent-light: rgba(34,197,94,0.1);
--bg: #FAFAF8;             /* 页面背景 */
--card-bg: #FFFFFF;        /* 卡片背景 */
--text: #1F2937;           /* 主文字 */
--text-secondary: #6B7280; /* 次要文字 */
--text-muted: #9CA3AF;     /* 弱化文字 */
--border: #E5E7EB;         /* 边框 */
--radius: 16px;            /* 卡片圆角 */
--radius-sm: 8px;          /* 小圆角 */
--input-height: 44px;      /* 输入框高度 */
```

---

## 启动方式

### 本地开发
```bash
# 1. 确保本地 MySQL 运行 (端口 3306, root/123456)
# 2. 启动后端
cd backend && pip install -r requirements.txt && python app.py
# → Flask 运行在 http://localhost:5000

# 3. 启动前端
cd frontend && npm install && npm run dev
# → Vite 运行在 http://localhost:3000, 代理 API 到 :5000
```

### Docker 部署
```bash
docker compose up --build
# → Nginx: http://localhost:8080
# → Backend: http://localhost:5001
# → MySQL: localhost:3308
```

---

## 路由表

| 路径 | 组件 | 权限 | 说明 |
|------|------|------|------|
| / | Home | 公开 | 商品广场 (网格分页) |
| /login | Login | guest | 登录 (密码+短信双模式) |
| /register | Register | guest | 注册 |
| /goods/:id | ProductDetail | 公开 | 商品详情 (图集/评价/价格走势) |
| /my-shop | MyShop | 需登录 | 我的店铺 (CRUD管理) |
| /cart | Cart | 需登录 | 购物车 (勾选结算) |
| /my-orders | MyOrders | 需登录 | 我的订单 (物流/评价) |
| /profile | Profile | 需登录 | 个人中心 (头像/密码/余额) |
