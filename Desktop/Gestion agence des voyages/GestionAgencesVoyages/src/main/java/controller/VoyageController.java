package controller;

import dao.VoyageDAO;
import entity.Voyage;
import java.sql.SQLException;
import java.util.List;

public class VoyageController {
    private final VoyageDAO voyageDAO;
    
    public VoyageController() {
        this.voyageDAO = new VoyageDAO();
    }

    public boolean ajouterVoyage(Voyage voyage) {
        try {
            return voyageDAO.create(voyage);
        } catch (SQLException e) {
            e.printStackTrace();
            return false;
        }
    }

    public boolean modifierVoyage(Voyage voyage) {
        try {
            return voyageDAO.update(voyage);
        } catch (SQLException e) {
            e.printStackTrace();
            return false;
        }
    }

    public boolean supprimerVoyage(int id) {
        try {
            return voyageDAO.delete(id);
        } catch (SQLException e) {
            e.printStackTrace();
            return false;
        }
    }

    public List<Voyage> listerTousVoyages() {
        try {
            return voyageDAO.getAll();
        } catch (SQLException e) {
            e.printStackTrace();
            return null;
        }
    }

    public List<Voyage> rechercherParDestination(String destination) {
        try {
            return voyageDAO.searchByDestination(destination);
        } catch (SQLException e) {
            e.printStackTrace();
            return null;
        }
    }
}