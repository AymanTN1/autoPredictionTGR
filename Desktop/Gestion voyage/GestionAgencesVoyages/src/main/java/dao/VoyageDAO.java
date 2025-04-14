package dao;

import entity.Voyage;
import java.sql.*;
import java.util.ArrayList;
import java.util.List;

public class VoyageDAO {
    Connection connection;

    public VoyageDAO() {
        // On récupère la connexion via votre classe de gestion de connexion (par exemple, db)
           connection = db.getConnection();

    }

    public boolean create(Voyage voyage) throws SQLException {
        String query = "INSERT INTO Voyage (destination, prix, aeroport_depart, aeroport_arrivee, nbr_places) VALUES (?, ?, ?, ?, ?)";
        try (PreparedStatement ps = connection.prepareStatement(query)) {
            ps.setString(1, voyage.getDestination());
            ps.setDouble(2, voyage.getPrix());
            ps.setString(3, voyage.getAeroportDepart());
            ps.setString(4, voyage.getAeroportArrivee());
            ps.setInt(5, voyage.getNbrPlaces());
            return ps.executeUpdate() > 0;
        }
    }

    public List<Voyage> getAll() throws SQLException {
        List<Voyage> voyages = new ArrayList<>();
        String query = "SELECT * FROM Voyage";
        try (Statement stmt = connection.createStatement();
             ResultSet rs = stmt.executeQuery(query)) {
            while (rs.next()) {
                voyages.add(mapResultSetToVoyage(rs));
            }
        }
        return voyages;
    }

    public boolean update(Voyage voyage) throws SQLException {
        String query = "UPDATE Voyage SET destination = ?, prix = ?, aeroport_depart = ?, aeroport_arrivee = ?, nbr_places = ? WHERE id = ?";
        try (PreparedStatement ps = connection.prepareStatement(query)) {
            ps.setString(1, voyage.getDestination());
            ps.setDouble(2, voyage.getPrix());
            ps.setString(3, voyage.getAeroportDepart());
            ps.setString(4, voyage.getAeroportArrivee());
            ps.setInt(5, voyage.getNbrPlaces());
            ps.setInt(6, voyage.getId());
            return ps.executeUpdate() > 0;
        }
    }

    public boolean delete(int id) throws SQLException {
        String query = "DELETE FROM Voyage WHERE id = ?";
        try (PreparedStatement ps = connection.prepareStatement(query)) {
            ps.setInt(1, id);
            return ps.executeUpdate() > 0;
        }
    }

    public List<Voyage> searchByDestination(String destination) throws SQLException {
        List<Voyage> voyages = new ArrayList<>();
        String query = "SELECT * FROM Voyage WHERE destination LIKE ?";
        try (PreparedStatement ps = connection.prepareStatement(query)) {
            ps.setString(1, destination + "%");
            ResultSet rs = ps.executeQuery();
            while (rs.next()) {
                voyages.add(mapResultSetToVoyage(rs));
            }
        }
        return voyages;
    }

    private Voyage mapResultSetToVoyage(ResultSet rs) throws SQLException {
        return new Voyage(
            rs.getInt("id"),
            rs.getString("destination"),
            rs.getDouble("prix"),
            rs.getString("aeroport_depart"),
            rs.getString("aeroport_arrivee"),
            rs.getInt("nbr_places")
        );
    }
}
