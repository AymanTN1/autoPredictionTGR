package TestDao;

import dao.ClientDAO;
import entity.Client;
import org.junit.jupiter.api.*;

import java.sql.SQLException;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
public class ClientDAOTest {

    private static ClientDAO clientDAO;
    private static Client testClient;

    @BeforeAll
    public static void setUpClass() {
        // Instanciation d'un ClientDAO pour l'ensemble des tests
        clientDAO = new ClientDAO();

        // Client de test (à adapter selon votre logique métier)
        testClient = new Client("C12345", "Dupont", "Jean", "P12345", "0601020304");
    }

    @Test
    @Order(1)
    @DisplayName("Test - Création d'un client dans la BDD")
    public void testCreateClient() {
        assertDoesNotThrow(() -> {
            boolean created = clientDAO.create(testClient);
            assertTrue(created, "Le client devrait être créé dans la base de données.");
        });
    }

    @Test
    @Order(2)
    @DisplayName("Test - Lecture de tous les clients")
    public void testGetAllClients() {
        assertDoesNotThrow(() -> {
            List<Client> clientList = clientDAO.getAll();
            // On vérifie qu'il y a au moins un client
            assertNotNull(clientList, "La liste ne doit pas être nulle.");
            assertFalse(clientList.isEmpty(), "La liste ne doit pas être vide après création d'un client.");
            // Vérifier que le client créé se trouve dans la liste
            boolean found = clientList.stream()
                                      .anyMatch(c -> c.getCin().equals(testClient.getCin()));
            assertTrue(found, "Le client créé doit apparaître dans la liste.");
        });
    }

    @Test
    @Order(3)
    @DisplayName("Test - Recherche de client par CIN")
    public void testSearchByCIN() {
        assertDoesNotThrow(() -> {
            List<Client> results = clientDAO.searchByCIN("C12345");
            assertNotNull(results, "La liste de résultats ne doit pas être nulle.");
            assertFalse(results.isEmpty(), "Au moins un client doit correspondre à la recherche par CIN.");
            assertEquals("C12345", results.get(0).getCin(),
                    "Le client récupéré doit avoir le CIN 'C12345'.");
        });
    }

    @Test
    @Order(4)
    @DisplayName("Test - Mise à jour des informations d'un client")
    public void testUpdateClient() {
        // On modifie quelques informations dans le client de test
        testClient.setNom("Durand");
        testClient.setPrenom("Marie");
        testClient.setTelephone("0701020304");

        assertDoesNotThrow(() -> {
            boolean updated = clientDAO.update(testClient);
            assertTrue(updated, "La mise à jour du client devrait réussir.");

            // Vérifier que les nouvelles infos sont bien prises en compte
            List<Client> results = clientDAO.searchByCIN(testClient.getCin());
            assertFalse(results.isEmpty(), "Le client mis à jour devrait être retrouvé par son CIN.");
            Client updatedClient = results.get(0);
            assertEquals("Durand", updatedClient.getNom(), "Le nom du client devrait être 'Durand'.");
            assertEquals("Marie", updatedClient.getPrenom(), "Le prénom du client devrait être 'Marie'.");
            assertEquals("0701020304", updatedClient.getTelephone(),
                    "Le numéro de téléphone devrait être '0701020304'.");
        });
    }

    @Test
    @Order(5)
    @DisplayName("Test - Suppression d'un client")
    public void testDeleteClient() {
        assertDoesNotThrow(() -> {
            boolean deleted = clientDAO.delete(testClient.getCin());
            assertTrue(deleted, "La suppression du client devrait réussir.");

            // Vérifier que le client n'apparaît plus
            List<Client> results = clientDAO.searchByCIN(testClient.getCin());
            assertTrue(results.isEmpty(), "Le client ne devrait plus exister dans la base.");
        });
    }
}
