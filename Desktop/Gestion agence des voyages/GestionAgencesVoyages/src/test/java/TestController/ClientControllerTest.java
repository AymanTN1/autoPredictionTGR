package TestController;

import controller.ClientController;
import entity.Client;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

class ClientControllerTest {
    private ClientController controller;
    private Client testClient;

    private static class StubClientDAO extends dao.ClientDAO {
        private Client storedClient;

        @Override
        public boolean create(Client client) {
            if(storedClient != null && storedClient.getCin().equals(client.getCin())) {
                return false; // Simule un doublon
            }
            storedClient = client;
            return true;
        }

        @Override
        public boolean update(Client client) {
            if(storedClient == null) return false;
            storedClient = client;
            return true;
        }

        @Override
        public boolean delete(String cin) {
            if(storedClient == null || !storedClient.getCin().equals(cin)) {
                return false;
            }
            storedClient = null;
            return true;
        }

        @Override
        public List<Client> getAll() {
            return storedClient != null ? List.of(storedClient) : List.of();
        }

        @Override
        public List<Client> searchByCIN(String cin) {
            return storedClient != null && storedClient.getCin().contains(cin) ? 
                List.of(storedClient) : 
                List.of();
        }
    }

    @BeforeEach
    void setUp() {
        // Injecte le stub dans le contrôleur
        controller = new ClientController(new StubClientDAO());
        testClient = new Client("C123", "Doe", "John", "P456", "0612345678");
    }

    @Test
    void ajouterClient_Success() {
        assertTrue(controller.ajouterClient(testClient));
    }

    @Test
    void ajouterClient_Duplicate_Failure() {
        controller.ajouterClient(testClient);
        assertFalse(controller.ajouterClient(testClient));
    }

    @Test
    void modifierClient_Success() {
        controller.ajouterClient(testClient);
        Client updated = new Client("C123", "Jane", "Doe", "P789", "0698765432");
        assertTrue(controller.modifierClient(updated));
    }

    @Test
    void supprimerClient_Success() {
        controller.ajouterClient(testClient);
        assertTrue(controller.supprimerClient("C123"));
    }

    @Test
    void listerClients_Success() {
        controller.ajouterClient(testClient);
        assertEquals(1, controller.listerTousClients().size());
    }

    @Test
    void rechercherParCIN_Success() {
        controller.ajouterClient(testClient);
        assertEquals(1, controller.rechercherParCIN("C1").size());
    }
}