SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";

CREATE TABLE `Bonuses` (
  `bonus_id` int(11) NOT NULL,
  `bonus_description` varchar(255) DEFAULT NULL,
  `bonus_answers` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`bonus_answers`))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Discord_users` (
  `discord_user_id` varchar(255) NOT NULL,
  `user_name` varchar(255) DEFAULT NULL,
  `user_discord_tag` int(4) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Matches` (
  `match_id` int(11) NOT NULL,
  `team_1` varchar(255) DEFAULT NULL,
  `team_2` varchar(255) DEFAULT NULL,
  `team_1_short` varchar(3) DEFAULT NULL,
  `team_2_short` varchar(3) DEFAULT NULL,
  `winner` varchar(255) DEFAULT NULL,
  `team_1_score` varchar(10) DEFAULT NULL,
  `team_2_score` varchar(10) DEFAULT NULL,
  `match_day` int(11) DEFAULT NULL,
  `match_week` int(11) DEFAULT NULL,
  `date` varchar(30) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Servers` (
  `discord_server_id` varchar(255) NOT NULL,
  `role_id` varchar(255) DEFAULT NULL,
  `server_name` varchar(255) DEFAULT NULL,
  `is_bonus` tinyint(1) DEFAULT NULL,
  `channel` varchar(255) DEFAULT NULL,
  `voting_message_id` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Server_bonuses` (
  `discord_server_id` varchar(255) DEFAULT NULL,
  `bonus_id` int(11) DEFAULT NULL,
  `week` varchar(255) DEFAULT NULL,
  `day` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Users` (
  `user_id` int(11) NOT NULL,
  `discord_server_id` varchar(255) DEFAULT NULL,
  `discord_user_id` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Users_bonus_votes` (
  `user_id` int(11) DEFAULT NULL,
  `bonus_id` int(11) DEFAULT NULL,
  `vote` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`vote`))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Users_points` (
  `user_id` int(11) DEFAULT NULL,
  `points` int(11) DEFAULT NULL,
  `answer_amount` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Users_votes` (
  `user_id` int(11) DEFAULT NULL,
  `match_id` int(11) DEFAULT NULL,
  `team_vote` varchar(3) DEFAULT NULL,
  `score_vote` varchar(3) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

ALTER TABLE `Bonuses`
  ADD PRIMARY KEY (`bonus_id`);

ALTER TABLE `Discord_users`
  ADD PRIMARY KEY (`discord_user_id`);

ALTER TABLE `Matches`
  ADD PRIMARY KEY (`match_id`);

ALTER TABLE `Servers`
  ADD PRIMARY KEY (`discord_server_id`);

ALTER TABLE `Users`
  ADD PRIMARY KEY (`user_id`),
  ADD KEY `discord_server_id` (`discord_server_id`),
  ADD KEY `discord_user_id` (`discord_user_id`);

ALTER TABLE `Bonuses`
  MODIFY `bonus_id` int(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE `Matches`
  MODIFY `match_id` int(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE `Users`
  MODIFY `user_id` int(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE `Users`
  ADD CONSTRAINT `Users_ibfk_1` FOREIGN KEY (`discord_server_id`) REFERENCES `Servers` (`discord_server_id`),
  ADD CONSTRAINT `Users_ibfk_2` FOREIGN KEY (`discord_user_id`) REFERENCES `Discord_users` (`discord_user_id`);
COMMIT;