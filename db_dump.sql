PRAGMA encoding='UTF-8';

--
-- Table structure for table `groups`
--

DROP TABLE IF EXISTS `groups`;
CREATE TABLE `groups` (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `tg_id` varchar(45) DEFAULT NULL,
    `vk_id` int(11) DEFAULT NULL,
    `last_post` int(11) DEFAULT -1,
    `pre_last_post` int(11) DEFAULT -1
);
