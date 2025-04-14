-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Hôte : 127.0.0.1
-- Généré le : jeu. 10 avr. 2025 à 11:35
-- Version du serveur : 10.4.32-MariaDB
-- Version de PHP : 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de données : `agence_voyage`
--

-- --------------------------------------------------------

--
-- Structure de la table `client`
--

CREATE TABLE `client` (
  `cin` varchar(20) NOT NULL,
  `nom` varchar(50) NOT NULL,
  `prenom` varchar(50) NOT NULL,
  `id_passport` varchar(50) NOT NULL,
  `telephone` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `client`
--

INSERT INTO `client` (`cin`, `nom`, `prenom`, `id_passport`, `telephone`) VALUES
('0987654321', 'Zidane', 'Zinedine', 'P87654321', '+213660987654'),
('1122334455', 'Benmessaoud', 'Lina', 'P11223344', '+213770112233'),
('1234567890', 'Benzema', 'Karim', 'P12345678', '+213550123456'),
('5566778899', 'Bouchenak', 'Mehdi', 'P55667788', '+213550665544'),
('6677889900', 'SRTYDFG', 'EDRFGHJ', 'R45678', '+234567');

-- --------------------------------------------------------

--
-- Structure de la table `reservation`
--

CREATE TABLE `reservation` (
  `id` int(11) NOT NULL,
  `cin_client` varchar(20) NOT NULL,
  `id_voyage` int(11) NOT NULL,
  `date_reservation` datetime DEFAULT current_timestamp(),
  `nbr_places_reservees` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `reservation`
--

INSERT INTO `reservation` (`id`, `cin_client`, `id_voyage`, `date_reservation`, `nbr_places_reservees`) VALUES
(1, '1234567890', 1, '2025-04-07 18:56:56', 2),
(2, '0987654321', 3, '2025-04-07 18:56:56', 1),
(3, '1122334455', 1, '2025-04-07 18:56:56', 4),
(4, '5566778899', 2, '2025-04-07 18:56:56', 3),
(5, '6677889900', 4, '2025-04-07 18:56:56', 2);

-- --------------------------------------------------------

--
-- Structure de la table `voyage`
--

CREATE TABLE `voyage` (
  `id` int(11) NOT NULL,
  `destination` varchar(100) NOT NULL,
  `date_depart` date NOT NULL,
  `periode_jours` int(11) NOT NULL,
  `prix` double NOT NULL,
  `aeroport_depart` varchar(100) NOT NULL,
  `aeroport_arrivee` varchar(100) NOT NULL,
  `date_heure_depart` datetime NOT NULL,
  `date_heure_arrivee` datetime NOT NULL,
  `nbr_places` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `voyage`
--

INSERT INTO `voyage` (`id`, `destination`, `date_depart`, `periode_jours`, `prix`, `aeroport_depart`, `aeroport_arrivee`, `date_heure_depart`, `date_heure_arrivee`, `nbr_places`) VALUES
(1, 'Paris', '2024-07-01', 7, 899.99, 'DAAG', 'CDG', '2024-07-01 08:00:00', '2024-07-01 11:30:00', 150),
(2, 'Istanbul', '2024-08-15', 5, 649.5, 'DAAG', 'IST', '2024-08-15 22:30:00', '2024-08-16 02:15:00', 200),
(3, 'Algerie', '2024-09-10', 4, 5678, 'Tunisie', 'Algé', '2024-09-10 10:45:00', '2024-09-10 16:20:00', 21),
(4, 'Madrid', '2024-06-20', 3, 450, 'DAAG', 'MAD', '2024-06-20 06:15:00', '2024-06-20 09:45:00', 120);

--
-- Index pour les tables déchargées
--

--
-- Index pour la table `client`
--
ALTER TABLE `client`
  ADD PRIMARY KEY (`cin`),
  ADD UNIQUE KEY `id_passport` (`id_passport`);

--
-- Index pour la table `reservation`
--
ALTER TABLE `reservation`
  ADD PRIMARY KEY (`id`),
  ADD KEY `cin_client` (`cin_client`),
  ADD KEY `id_voyage` (`id_voyage`);

--
-- Index pour la table `voyage`
--
ALTER TABLE `voyage`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT pour les tables déchargées
--

--
-- AUTO_INCREMENT pour la table `reservation`
--
ALTER TABLE `reservation`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT pour la table `voyage`
--
ALTER TABLE `voyage`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- Contraintes pour les tables déchargées
--

--
-- Contraintes pour la table `reservation`
--
ALTER TABLE `reservation`
  ADD CONSTRAINT `reservation_ibfk_1` FOREIGN KEY (`cin_client`) REFERENCES `client` (`cin`),
  ADD CONSTRAINT `reservation_ibfk_2` FOREIGN KEY (`id_voyage`) REFERENCES `voyage` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
