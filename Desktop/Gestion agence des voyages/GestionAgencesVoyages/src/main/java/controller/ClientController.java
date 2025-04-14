package controller;

import dao.ClientDAO;
import entity.Client;
import java.sql.SQLException;
import java.util.List;

public class ClientController {
    private final ClientDAO clientDAO;
    
    // Constructeur pour l'injection de dépendance
    public ClientController(ClientDAO dao) {
        this.clientDAO = dao;
    }

    
    public ClientController() {
        this.clientDAO = new ClientDAO();
    }

    public boolean ajouterClient(Client client) {
        try {
            return clientDAO.create(client);
        } catch (SQLException e) {
            e.printStackTrace();
            return false;
        }
    }

    public boolean modifierClient(Client client) {
        try {
            return clientDAO.update(client);
        } catch (SQLException e) {
            e.printStackTrace();
            return false;
        }
    }

    public boolean supprimerClient(String cin) {
        try {
            return clientDAO.delete(cin);
        } catch (SQLException e) {
            e.printStackTrace();
            return false;
        }
    }

    public List<Client> listerTousClients() {
        try {
           List<Client> l =  clientDAO.getAll();
            System.out.println(l);
           return l;
        } catch (SQLException e) {
            e.printStackTrace();
            return null;
        }
    }

    public List<Client> rechercherParCIN(String cin) {
        try {
            return clientDAO.searchByCIN(cin);
        } catch (SQLException e) {
            e.printStackTrace();
            return null;
        }
    }
}