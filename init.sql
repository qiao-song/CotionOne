CREATE DATABASE IF NOT EXISTS tbao
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE tbao;

CREATE TABLE IF NOT EXISTS users (
    id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(50)  NOT NULL UNIQUE COMMENT '用户名',
    phone         VARCHAR(20)  NOT NULL UNIQUE COMMENT '手机号',
    password_hash VARCHAR(255) NOT NULL COMMENT 'bcrypt密码哈希',
    avatar        VARCHAR(500) DEFAULT '/static/default.png' COMMENT '头像URL',
    balance       DECIMAL(10,2) DEFAULT 200.00 COMMENT '账户余额',
    created_at    DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_phone (phone)
) ENGINE=InnoDB COMMENT='用户表';

CREATE TABLE IF NOT EXISTS goods (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    title       VARCHAR(200)   NOT NULL COMMENT '商品标题',
    price       DECIMAL(10,2)  NOT NULL COMMENT '价格',
    description TEXT           DEFAULT NULL COMMENT '商品描述',
    images      JSON           DEFAULT NULL COMMENT '图片URL数组',
    status      TINYINT        DEFAULT 1 COMMENT '状态: 1=上架, 0=下架',
    video       VARCHAR(500)   DEFAULT NULL COMMENT '商品视频URL',
    video_likes INT            DEFAULT 0 COMMENT '视频点赞数',
    video_shares INT           DEFAULT 0 COMMENT '视频分享数',
    tags         JSON           DEFAULT NULL COMMENT '商品标签数组',
    seller_id   BIGINT         NOT NULL COMMENT '卖家ID',
    created_at  DATETIME       DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME       DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at  DATETIME       DEFAULT NULL COMMENT '软删除时间',
    FOREIGN KEY (seller_id) REFERENCES users(id),
    INDEX idx_seller (seller_id),
    INDEX idx_status_created (status, created_at)
) ENGINE=InnoDB COMMENT='商品表';

CREATE TABLE IF NOT EXISTS orders (
    id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    buyer_id      BIGINT         NOT NULL COMMENT '买家ID',
    goods_id      BIGINT         NOT NULL COMMENT '商品ID',
    goods_title   VARCHAR(200)   NOT NULL COMMENT '商品标题快照',
    goods_price   DECIMAL(10,2)  NOT NULL COMMENT '成交价快照',
    goods_image   VARCHAR(500)   DEFAULT NULL COMMENT '商品图片快照',
    quantity      INT            DEFAULT 1 COMMENT '数量',
    total_amount  DECIMAL(10,2)  NOT NULL COMMENT '总金额',
    status        VARCHAR(20)    DEFAULT 'pending' COMMENT 'pending=未发货, shipped=运输中, received=已签收, returned=已退货',
    logistics     JSON           DEFAULT NULL COMMENT '物流记录',
    created_at    DATETIME       DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME       DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (buyer_id) REFERENCES users(id),
    FOREIGN KEY (goods_id) REFERENCES goods(id),
    INDEX idx_buyer (buyer_id),
    INDEX idx_goods (goods_id),
    INDEX idx_status (status)
) ENGINE=InnoDB COMMENT='订单表';

CREATE TABLE IF NOT EXISTS reviews (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id     BIGINT NOT NULL COMMENT '评论者ID',
    goods_id    BIGINT NOT NULL COMMENT '商品ID',
    order_id    BIGINT NOT NULL COMMENT '订单ID',
    rating      TINYINT DEFAULT 5 COMMENT '评分 1-5',
    content     TEXT DEFAULT NULL COMMENT '评论内容',
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (goods_id) REFERENCES goods(id),
    FOREIGN KEY (order_id) REFERENCES orders(id),
    INDEX idx_goods (goods_id),
    INDEX idx_user (user_id),
    UNIQUE KEY uk_order (order_id) COMMENT '一个订单只能评论一次'
) ENGINE=InnoDB COMMENT='商品评论表';

CREATE TABLE IF NOT EXISTS posts (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id     BIGINT NOT NULL COMMENT '发布者ID',
    content     TEXT NOT NULL COMMENT '日志内容',
    images      JSON DEFAULT NULL COMMENT '图片URL数组',
    video       VARCHAR(500) DEFAULT NULL COMMENT '视频URL',
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_user (user_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='种草日志';

CREATE TABLE IF NOT EXISTS emojis (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(50) NOT NULL COMMENT '表情名称',
    image_url       VARCHAR(500) NOT NULL COMMENT '表情图片URL',
    uploader_id     BIGINT NOT NULL COMMENT '上传者ID',
    download_count  INT DEFAULT 0 COMMENT '下载次数',
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (uploader_id) REFERENCES users(id),
    INDEX idx_download (download_count),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Tbao表情包';
