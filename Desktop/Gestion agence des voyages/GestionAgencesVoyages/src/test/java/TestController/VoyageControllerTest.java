package TestController;
import controller.VoyageController;
import entity.Voyage;
import static org.junit.jupiter.api.Assertions.*;
import org.junit.jupiter.api.*;
import java.util.List;

public class VoyageControllerTest {

    private VoyageController controller;

    @BeforeEach
    public void setUp() {
        controller = new VoyageController();
        // Si possible, vous pouvez vider la table voyages ici pour un état propre de test.
        // Par exemple, appeler une méthode de nettoyage via le DAO (non montré ici).
    }
    
    @Test
    public void testAjouterVoyage() {
        // Création d'un voyage avec des valeurs de test
        Voyage voyage = new Voyage("Test Destination", 100.0, "TestDep", "TestArr", 50);
        boolean ajoutReussi = controller.ajouterVoyage(voyage);
        
        assertTrue(ajoutReussi, "L'ajout du voyage devrait réussir");
        
        // On vérifie ensuite que le voyage apparait dans la liste
        List<Voyage> voyages = controller.rechercherParDestination("Test Destination");
        assertNotNull(voyages, "La recherche ne doit pas retourner null");
        boolean trouve = voyages.stream().anyMatch(v -> 
                v.getDestination().equals("Test Destination") &&
                v.getPrix() == 100.0 &&
                v.getAeroportDepart().equals("TestDep") &&
                v.getAeroportArrivee().equals("TestArr") &&
                v.getNbrPlaces() == 50);
        assertTrue(trouve, "Le voyage ajouté doit se retrouver dans la liste");
    }
    
    @Test
    public void testModifierVoyage() {
        // Ajout d'un voyage pour pouvoir le modifier par la suite
        Voyage voyage = new Voyage("Modif Destination", 200.0, "Dep", "Arr", 75);
        boolean ajoutReussi = controller.ajouterVoyage(voyage);
        assertTrue(ajoutReussi, "L'ajout du voyage avant modification doit réussir");
        
        // Récupérer le voyage ajouté afin d'obtenir son ID (attention : cela suppose que la recherche retourne le bon enregistrement)
        List<Voyage> voyages = controller.rechercherParDestination("Modif Destination");
        assertFalse(voyages.isEmpty(), "Le voyage ajouté doit être présent pour modification");
        Voyage voyageToModify = voyages.get(0);
        
        // Modifier certains attributs
        voyageToModify.setPrix(250.0);
        voyageToModify.setNbrPlaces(80);
        
        boolean modifReussie = controller.modifierVoyage(voyageToModify);
        assertTrue(modifReussie, "La modification du voyage devrait réussir");
        
        // Vérifier que les modifications sont bien enregistrées
        List<Voyage> updatedVoyages = controller.rechercherParDestination("Modif Destination");
        assertFalse(updatedVoyages.isEmpty(), "La recherche après modification ne doit pas être vide");
        Voyage updatedVoyage = updatedVoyages.get(0);
        assertEquals(250.0, updatedVoyage.getPrix(), "Le prix du voyage doit être mis à jour à 250.0");
        assertEquals(80, updatedVoyage.getNbrPlaces(), "Le nombre de places doit être mis à jour à 80");
    }
    
    @Test
    public void testSupprimerVoyage() {
        // Ajout d'un voyage pour pouvoir le supprimer
        Voyage voyage = new Voyage("Delete Destination", 300.0, "Dep", "Arr", 90);
        boolean ajoutReussi = controller.ajouterVoyage(voyage);
        assertTrue(ajoutReussi, "L'ajout du voyage à supprimer doit réussir");
        
        // Récupération de l'ID du voyage à supprimer
        List<Voyage> voyages = controller.rechercherParDestination("Delete Destination");
        assertFalse(voyages.isEmpty(), "Le voyage doit être trouvé pour suppression");
        int id = voyages.get(0).getId();
        
        // Exécution de la suppression
        boolean suppressionReussie = controller.supprimerVoyage(id);
        assertTrue(suppressionReussie, "La suppression du voyage devrait réussir");
        
        // Vérification que le voyage n'est plus présent
        List<Voyage> voyagesApresSuppression = controller.rechercherParDestination("Delete Destination");
        assertTrue(voyagesApresSuppression.isEmpty(), "Le voyage doit être supprimé de la base");
    }
    
    @Test
    public void testListerTousVoyages() {
        // On peut ajouter un voyage de test afin d'avoir un enregistrement connu dans la liste
        Voyage voyage = new Voyage("List Destination", 150.0, "Dep", "Arr", 60);
        controller.ajouterVoyage(voyage);
        
        List<Voyage> voyages = controller.listerTousVoyages();
        assertNotNull(voyages, "La méthode listerTousVoyages ne doit pas retourner null");
        // On vérifie au moins que la liste contient un enregistrement avec la destination de test
        boolean trouve = voyages.stream().anyMatch(v -> v.getDestination().equals("List Destination"));
        assertTrue(trouve, "La liste des voyages doit contenir le voyage de test");
    }
    
    @Test
    public void testRechercherParDestination() {
        // Ajout d'un voyage avec une destination spécifique
        String destinationRecherchee = "Search Destination";
        Voyage voyage = new Voyage(destinationRecherchee, 150.0, "Dep", "Arr", 60);
        boolean ajoutReussi = controller.ajouterVoyage(voyage);
        assertTrue(ajoutReussi, "L'ajout du voyage pour le test de recherche doit réussir");
        
        // Recherche par destination
        List<Voyage> voyages = controller.rechercherParDestination(destinationRecherchee);
        assertNotNull(voyages, "La recherche ne doit pas retourner null");
        assertFalse(voyages.isEmpty(), "La recherche doit retourner au moins un résultat");
        // Vérifier que la destination du voyage trouvé correspond à celle recherchée
        boolean correspond = voyages.stream().anyMatch(v -> destinationRecherchee.equals(v.getDestination()));
        assertTrue(correspond, "Le voyage recherché doit avoir la destination correspondante");
    }
}
