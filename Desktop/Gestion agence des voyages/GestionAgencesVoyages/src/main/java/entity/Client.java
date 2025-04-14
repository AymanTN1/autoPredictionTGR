package entity;

public class Client {
    private String cin;
    private String nom;
    private String prenom;
    private String idPassport;
    private String telephone;

    public Client() {
    }

    public Client(String cin, String nom, String prenom, String idPassport, String telephone) {
        this.cin = cin;
        this.nom = nom;
        this.prenom = prenom;
        this.idPassport = idPassport;
        this.telephone = telephone;
    }

    // Getters & Setters
    public String getCin() { return cin; }
    public void setCin(String cin) { this.cin = cin; }

    public String getNom() { return nom; }
    public void setNom(String nom) { this.nom = nom; }

    public String getPrenom() { return prenom; }
    public void setPrenom(String prenom) { this.prenom = prenom; }

    public String getIdPassport() { return idPassport; }
    public void setIdPassport(String idPassport) { this.idPassport = idPassport; }

    public String getTelephone() { return telephone; }
    public void setTelephone(String telephone) { this.telephone = telephone; }

    @Override
    public String toString() {
        return "Client{" +
                "cin='" + cin + '\'' +
                ", nom='" + nom + '\'' +
                ", prenom='" + prenom + '\'' +
                ", idPassport='" + idPassport + '\'' +
                ", telephone='" + telephone + '\'' +
                '}';
    }

    public Object[] toArray() {
        return new Object[]{cin, nom, prenom, idPassport, telephone};
    }
}