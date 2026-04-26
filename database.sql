-- Script consolidado para criacao manual do schema no MySQL Workbench
-- Baseado nas migracoes V1..V11

CREATE DATABASE IF NOT EXISTS lottusdb
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE lottusdb;

CREATE TABLE IF NOT EXISTS turmas (
    id BIGINT NOT NULL AUTO_INCREMENT,
    serie VARCHAR(50) NOT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS alunos (
    id BIGINT NOT NULL AUTO_INCREMENT,
    matricula VARCHAR(50) NOT NULL,
    nome VARCHAR(255) NOT NULL,
    qtd_bonus DOUBLE NOT NULL DEFAULT 0,
    qtd_livros_lidos INTEGER NOT NULL DEFAULT 0,
    turma_id BIGINT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uk_aluno_matricula (matricula),
    INDEX idx_aluno_turma (turma_id),
    CONSTRAINT fk_aluno_turma FOREIGN KEY (turma_id) REFERENCES turmas(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS usuarios (
    id BIGINT NOT NULL AUTO_INCREMENT,
    nome VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    telefone VARCHAR(20) NULL,
    senha VARCHAR(255) NOT NULL,
    dt_registro TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    id_avatar VARCHAR(100) NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uk_usuario_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS livros (
    id BIGINT NOT NULL AUTO_INCREMENT,
    titulo VARCHAR(255) NOT NULL,
    autor VARCHAR(255) NULL,
    sinopse TEXT NULL,
    categoria VARCHAR(255) NULL,
    isbn VARCHAR(20) NULL,
    total_paginas INT NULL,
    PRIMARY KEY (id),
    INDEX idx_livros_categoria_titulo (categoria, titulo),
    CONSTRAINT uk_livro_isbn UNIQUE (isbn)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS emprestimos (
    id BIGINT NOT NULL AUTO_INCREMENT,
    aluno_id BIGINT NOT NULL,
    livro_id BIGINT NOT NULL,
    data_emprestimo DATE NOT NULL,
    data_devolucao_prevista DATE NOT NULL,
    data_devolucao_efetiva DATE NULL,
    dias_atrasados INT NOT NULL DEFAULT 0,
    status_emprestimo VARCHAR(20) NOT NULL DEFAULT 'ATIVO',
    PRIMARY KEY (id),
    INDEX idx_emp_aluno (aluno_id),
    INDEX idx_emp_livro (livro_id),
    INDEX idx_emp_status (status_emprestimo),
    INDEX idx_emp_aluno_livro (aluno_id, livro_id),
    INDEX idx_emp_livro_status (livro_id, status_emprestimo),
    INDEX idx_emp_aluno_data (aluno_id, data_emprestimo),
    CONSTRAINT fk_emp_aluno FOREIGN KEY (aluno_id) REFERENCES alunos(id) ON DELETE CASCADE,
    CONSTRAINT fk_emp_livro FOREIGN KEY (livro_id) REFERENCES livros(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS refresh_tokens (
    id BIGINT NOT NULL AUTO_INCREMENT,
    token_hash VARCHAR(255) NOT NULL,
    user_id BIGINT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    revoked BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_refresh_token_hash (token_hash),
    INDEX idx_refresh_user (user_id),
    INDEX idx_refresh_expires (expires_at),
    CONSTRAINT fk_refresh_user FOREIGN KEY (user_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS usuario_aluno (
    usuario_id BIGINT NOT NULL,
    aluno_id BIGINT NOT NULL,
    PRIMARY KEY (usuario_id, aluno_id),
    INDEX idx_ua_aluno (aluno_id),
    CONSTRAINT fk_ua_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    CONSTRAINT fk_ua_aluno FOREIGN KEY (aluno_id) REFERENCES alunos(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS metas (
    id BIGINT NOT NULL AUTO_INCREMENT,
    aluno_id BIGINT NOT NULL,
    criado_por_usuario_id BIGINT NOT NULL,
    tipo VARCHAR(40) NOT NULL,
    titulo VARCHAR(150) NOT NULL,
    descricao VARCHAR(500) NULL,
    tipo_validacao VARCHAR(20) NOT NULL,
    valor_alvo INT NOT NULL DEFAULT 1,
    valor_atual INT NOT NULL DEFAULT 0,
    filtro_valor VARCHAR(150) NULL,
    data_inicio DATE NOT NULL,
    data_fim DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ATIVA',
    concluida_em TIMESTAMP NULL,
    criada_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizada_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_meta_aluno (aluno_id),
    INDEX idx_meta_criador (criado_por_usuario_id),
    INDEX idx_meta_status (status),
    INDEX idx_meta_janela (data_inicio, data_fim),
    CONSTRAINT fk_meta_aluno FOREIGN KEY (aluno_id) REFERENCES alunos(id) ON DELETE CASCADE,
    CONSTRAINT fk_meta_usuario FOREIGN KEY (criado_por_usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO turmas (id, serie) VALUES
    (1, '6A'),
    (2, '6B'),
    (3, '7A');

INSERT IGNORE INTO alunos (id, matricula, nome, qtd_bonus, qtd_livros_lidos, turma_id) VALUES
    (1, '2026001', 'Ana Souza', 12.5, 3, 1),
    (2, '2026002', 'Bruno Lima', 5.0, 1, 1),
    (3, '2026003', 'Carla Mendes', 18.0, 5, 2),
    (4, '2026004', 'Diego Alves', 2.0, 0, 3);

INSERT IGNORE INTO usuarios (id, nome, email, telefone, senha, id_avatar) VALUES
    (1, 'Bibliotecaria Maria', 'maria@lottus.local', '11999990001', '$2b$12$hashfake001', 'avatar_01'),
    (2, 'Professor Joao', 'joao@lottus.local', '11999990002', '$2b$12$hashfake002', 'avatar_02'),
    (3, 'Coordenadora Paula', 'paula@lottus.local', '11999990003', '$2b$12$hashfake003', 'avatar_03');

INSERT IGNORE INTO livros (id, titulo, autor, sinopse, categoria, isbn, total_paginas) VALUES
    (1, 'O Pequeno Principe', 'Antoine de Saint-Exupery', 'Classico sobre amizade e sentido da vida.', 'Literatura', '9788574061234', 96),
    (2, 'Dom Casmurro', 'Machado de Assis', 'Romance brasileiro sobre memoria e duvida.', 'Classicos Brasileiros', '9788503012301', 256),
    (3, 'A Volta ao Mundo em 80 Dias', 'Julio Verne', 'Aventura de viagem e desafios.', 'Aventura', '9788535920013', 240),
    (4, 'Capitaes da Areia', 'Jorge Amado', 'Historia de jovens em Salvador.', 'Romance', '9788535923458', 288);

INSERT IGNORE INTO usuario_aluno (usuario_id, aluno_id) VALUES
    (2, 1),
    (2, 2),
    (2, 3),
    (3, 4);

INSERT IGNORE INTO emprestimos (
    id,
    aluno_id,
    livro_id,
    data_emprestimo,
    data_devolucao_prevista,
    data_devolucao_efetiva,
    dias_atrasados,
    status_emprestimo
) VALUES
    (1, 1, 1, '2026-04-01', '2026-04-15', '2026-04-14', 0, 'DEVOLVIDO'),
    (2, 2, 2, '2026-04-10', '2026-04-24', NULL, 0, 'ATIVO'),
    (3, 3, 3, '2026-03-20', '2026-04-03', '2026-04-07', 4, 'DEVOLVIDO'),
    (4, 4, 4, '2026-04-12', '2026-04-26', NULL, 0, 'ATIVO');

INSERT IGNORE INTO refresh_tokens (id, token_hash, user_id, expires_at, revoked) VALUES
    (1, 'token_hash_maria_001', 1, '2026-05-01 10:00:00', FALSE),
    (2, 'token_hash_joao_001', 2, '2026-05-01 10:00:00', FALSE),
    (3, 'token_hash_paula_001', 3, '2026-05-01 10:00:00', TRUE);

INSERT IGNORE INTO metas (
    id,
    aluno_id,
    criado_por_usuario_id,
    tipo,
    titulo,
    descricao,
    tipo_validacao,
    valor_alvo,
    valor_atual,
    filtro_valor,
    data_inicio,
    data_fim,
    status,
    concluida_em
) VALUES
    (1, 1, 2, 'LEITURA_LIVROS', 'Ler 3 livros no mes', 'Meta mensal de leitura para abril.', 'QUANTIDADE', 3, 2, 'categoria=Literatura', '2026-04-01', '2026-04-30', 'ATIVA', NULL),
    (2, 3, 2, 'PAGINAS_LIDAS', 'Ler 400 paginas', 'Foco em constancia de leitura.', 'QUANTIDADE', 400, 400, 'categoria=Aventura', '2026-03-01', '2026-03-31', 'CONCLUIDA', '2026-03-29 18:20:00'),
    (3, 4, 3, 'FREQUENCIA_BIBLIOTECA', 'Visitar biblioteca 4 vezes', 'Estimular rotina de leitura.', 'QUANTIDADE', 4, 1, NULL, '2026-04-01', '2026-04-30', 'ATIVA', NULL);