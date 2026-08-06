CREATE DATABASE IF NOT EXISTS linux_lab
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;

USE linux_lab;

CREATE TABLE IF NOT EXISTS lab_events (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  event_id CHAR(36) NOT NULL,
  intern_name VARCHAR(64) NOT NULL,
  event_type VARCHAR(64) NOT NULL,
  payload JSON NOT NULL,
  created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  UNIQUE KEY uq_lab_events_event_id (event_id),
  KEY idx_lab_events_created_at (created_at)
) ENGINE=InnoDB;
