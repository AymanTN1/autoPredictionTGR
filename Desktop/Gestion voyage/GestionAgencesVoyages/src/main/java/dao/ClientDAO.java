package dao;

import entity.Client;
import java.sql.*;
import java.util.ArrayList;
import java.util.List;

public class ClientDAO {
    Connection connection;

    public ClientDAO() {
        // Constructeur vide car pas d'initialisation nécessaire
        connection = db.getConnection();
    }

    public boolean create(Client client) throws SQLException {
        String query = "INSERT INTO Client (cin, nom, prenom, id_passport, telephone) VALUES (?, ?, ?, ?, ?)";
        
        try (
             PreparedStatement ps = connection.prepareStatement(query)) {
            
            ps.setString(1, client.getCin());
            ps.setString(2, client.getNom());
            ps.setString(3, client.getPrenom());
            ps.setString(4, client.getIdPassport());
            ps.setString(5, client.getTelephone());
            
            return ps.executeUpdate() > 0;
        }
    }

    public List<Client> getAll() throws SQLException {
        List<Client> clients = new ArrayList<>();
        String query = "SELECT * FROM Client";
        
        try (
             Statement stmt = connection.createStatement();
             ResultSet rs = stmt.executeQuery(query)) {
            
            while (rs.next()) {
                clients.add(mapResultSetToClient(rs));
            }
        }
        
        System.out.println(clients);
        return clients;
    }

    public boolean update(Client client) throws SQLException {
        String query = "UPDATE Client SET nom=?, prenom=?, id_passport=?, telephone=? WHERE cin=?";
        
        try ( 
             PreparedStatement ps = connection.prepareStatement(query)) {
            
            ps.setString(1, client.getNom());
            ps.setString(2, client.getPrenom());
            ps.setString(3, client.getIdPassport());
            ps.setString(4, client.getTelephone());
            ps.setString(5, client.getCin());
            
            return ps.executeUpdate() > 0;
        }
    }

    public boolean delete(String cin) throws SQLException {
        String query = "DELETE FROM Client WHERE cin like ?";
        
        try ( 
             PreparedStatement ps = connection.prepareStatement(query)) {
            
            ps.setString(1, cin);
            return ps.executeUpdate() > 0;
        }
    }

    public List<Client> searchByCIN(String cin) throws SQLException {
        List<Client> clients = new ArrayList<>();
        String query = "SELECT * FROM Client WHERE cin LIKE ?";
        
        try (
             PreparedStatement ps = connection.prepareStatement(query)) {
            
            ps.setString(1,  cin + "%");
            ResultSet rs = ps.executeQuery();
            
            while (rs.next()) {
                clients.add(mapResultSetToClient(rs));
            }
        }
        return clients;
    }

    private Client mapResultSetToClient(ResultSet rs) throws SQLException {
        return new Client(
            rs.getString("cin"),
            rs.getString("nom"),
            rs.getString("prenom"),
            rs.getString("id_passport"),
            rs.getString("telephone")
        );
    }
}