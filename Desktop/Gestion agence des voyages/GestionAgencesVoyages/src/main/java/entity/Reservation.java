package entity;

import java.time.LocalDateTime;

public class Reservation {
    private int id;
    private Client client;
    private Voyage voyage;
    private LocalDateTime dateReservation;
    private int nbrPlacesReservees;

    public Reservation(int id, Client client, Voyage voyage, int nbrPlacesReservees) {
        this.id = id;
        this.client = client;
        this.voyage = voyage;
        this.dateReservation = LocalDateTime.now();
        this.nbrPlacesReservees = nbrPlacesReservees;
    }

    // Getters
    public int getId() { return id; }
    public Client getClient() { return client; }
    public Voyage getVoyage() { return voyage; }
    public LocalDateTime getDateReservation() { return dateReservation; }
    public int getNbrPlacesReservees() { return nbrPlacesReservees; }

    // Setters
    public void setClient(Client client) { this.client = client; }
    public void setVoyage(Voyage voyage) { this.voyage = voyage; }
    public void setNbrPlacesReservees(int nbrPlacesReservees) { 
        this.nbrPlacesReservees = nbrPlacesReservees; 
    }
}