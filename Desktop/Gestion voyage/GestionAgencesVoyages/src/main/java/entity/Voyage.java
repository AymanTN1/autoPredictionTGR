package entity;

public class Voyage {
    private int id;
    private String destination;
    private double prix;
    private String aeroportDepart;
    private String aeroportArrivee;
    private int nbrPlaces;

    // Constructeur pour création (sans ID)
    public Voyage(String destination, double prix, 
                String aeroportDepart, String aeroportArrivee, int nbrPlaces) {
        this.destination = destination;
        this.prix = prix;
        this.aeroportDepart = aeroportDepart;
        this.aeroportArrivee = aeroportArrivee;
        this.nbrPlaces = nbrPlaces;
    }

    // Constructeur pour récupération BD (avec ID)
    public Voyage(int id, String destination, double prix, 
                String aeroportDepart, String aeroportArrivee, int nbrPlaces) {
        this.id = id;
        this.destination = destination;
        this.prix = prix;
        this.aeroportDepart = aeroportDepart;
        this.aeroportArrivee = aeroportArrivee;
        this.nbrPlaces = nbrPlaces;
    }

    // Getters & Setters
    public int getId() { return id; }
    public void setId(int id) { this.id = id; }

    public String getDestination() { return destination; }
    public void setDestination(String destination) { this.destination = destination; }

    public double getPrix() { return prix; }
    public void setPrix(double prix) { this.prix = prix; }

    public String getAeroportDepart() { return aeroportDepart; }
    public void setAeroportDepart(String aeroportDepart) { this.aeroportDepart = aeroportDepart; }

    public String getAeroportArrivee() { return aeroportArrivee; }
    public void setAeroportArrivee(String aeroportArrivee) { this.aeroportArrivee = aeroportArrivee; }

    public int getNbrPlaces() { return nbrPlaces; }
    public void setNbrPlaces(int nbrPlaces) { this.nbrPlaces = nbrPlaces; }

    @Override
    public String toString() {
        return "Voyage{" +
                "id=" + id +
                ", destination='" + destination + '\'' +
                ", prix=" + prix +
                ", aeroportDepart='" + aeroportDepart + '\'' +
                ", aeroportArrivee='" + aeroportArrivee + '\'' +
                ", nbrPlaces=" + nbrPlaces +
                '}';
    }

    public Object[] toArray() {
        return new Object[]{id, destination, prix, aeroportDepart, aeroportArrivee, nbrPlaces};
    }
}