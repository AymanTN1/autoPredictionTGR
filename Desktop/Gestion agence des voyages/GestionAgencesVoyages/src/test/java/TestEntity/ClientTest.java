package TestEntity;

import entity.Client;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class ClientTest {

    @Test
    void testDefaultConstructor() {
        Client client = new Client();
        
        assertNull(client.getCin());
        assertNull(client.getNom());
        assertNull(client.getPrenom());
        assertNull(client.getIdPassport());
        assertNull(client.getTelephone());
    }

    @Test
    void testParameterizedConstructor() {
        Client client = new Client(
            "C123456",
            "Dupont",
            "Jean",
            "P987654",
            "0612345678"
        );
        
        assertEquals("C123456", client.getCin());
        assertEquals("Dupont", client.getNom());
        assertEquals("Jean", client.getPrenom());
        assertEquals("P987654", client.getIdPassport());
        assertEquals("0612345678", client.getTelephone());
    }

    @Test
    void testSettersAndGetters() {
        Client client = new Client();
        
        client.setCin("C654321");
        client.setNom("Martin");
        client.setPrenom("Sophie");
        client.setIdPassport("P123456");
        client.setTelephone("0698765432");
        
        assertEquals("C654321", client.getCin());
        assertEquals("Martin", client.getNom());
        assertEquals("Sophie", client.getPrenom());
        assertEquals("P123456", client.getIdPassport());
        assertEquals("0698765432", client.getTelephone());
    }

    @Test
    void testToString() {
        Client client = new Client(
            "C111",
            "Durand",
            "Marie",
            "P111",
            "0611111111"
        );
        
        String expected = "Client{"
            + "cin='C111'"
            + ", nom='Durand'"
            + ", prenom='Marie'"
            + ", idPassport='P111'"
            + ", telephone='0611111111'"
            + "}";
        
        assertEquals(expected, client.toString());
    }

    @Test
    void testToArray() {
        Client client = new Client(
            "C222",
            "Leroy",
            "Paul",
            "P222",
            "0622222222"
        );
        
        Object[] expected = {"C222", "Leroy", "Paul", "P222", "0622222222"};
        assertArrayEquals(expected, client.toArray());
    }

    @Test
    void testEquality() {
        Client client1 = new Client("C123", "Doe", "John", "P456", "0612345678");
        Client client2 = new Client("C123", "Doe", "John", "P456", "0612345678");
        
        assertEquals(client1.getCin(), client2.getCin());
        assertEquals(client1.getNom(), client2.getNom());
        assertEquals(client1.getPrenom(), client2.getPrenom());
        assertEquals(client1.getIdPassport(), client2.getIdPassport());
        assertEquals(client1.getTelephone(), client2.getTelephone());
    }

    @Test
    void testTelephoneWithSpecialCharacters() {
        Client client = new Client();
        String phoneNumber = "+212-612-345678";
        client.setTelephone(phoneNumber);
        
        assertEquals(phoneNumber, client.getTelephone());
    }
}