package TestEntity;
import entity.Voyage;
import static org.junit.jupiter.api.Assertions.*;
import org.junit.jupiter.api.Test;

public class VoyagesTest {

    @Test
    public void testConstructorWithoutId() {
        // Création d'un voyage sans spécifier l'ID
        Voyage voyage = new Voyage("Paris", 299.99, "CDG", "Orly", 150);
        
        // Comme l'ID n'est pas défini dans ce constructeur,
        // on vérifie que la valeur par défaut est 0
        assertEquals(0, voyage.getId(), "L'ID doit être 0 par défaut");
        assertEquals("Paris", voyage.getDestination());
        assertEquals(299.99, voyage.getPrix());
        assertEquals("CDG", voyage.getAeroportDepart());
        assertEquals("Orly", voyage.getAeroportArrivee());
        assertEquals(150, voyage.getNbrPlaces());
    }
    
    @Test
    public void testConstructorWithId() {
        // Création d'un voyage en spécifiant l'ID
        Voyage voyage = new Voyage(1, "Londres", 199.99, "LGW", "LHR", 100);
        
        assertEquals(1, voyage.getId());
        assertEquals("Londres", voyage.getDestination());
        assertEquals(199.99, voyage.getPrix());
        assertEquals("LGW", voyage.getAeroportDepart());
        assertEquals("LHR", voyage.getAeroportArrivee());
        assertEquals(100, voyage.getNbrPlaces());
    }
    
    @Test
    public void testSettersAndGetters() {
        Voyage voyage = new Voyage("Rome", 150.50, "FCO", "Ciampino", 80);
        
        // Modifier les valeurs via les setters
        voyage.setId(5);
        voyage.setDestination("Milan");
        voyage.setPrix(175.75);
        voyage.setAeroportDepart("MXP");
        voyage.setAeroportArrivee("Malpensa");
        voyage.setNbrPlaces(120);
        
        // Vérifier les valeurs via les getters
        assertEquals(5, voyage.getId());
        assertEquals("Milan", voyage.getDestination());
        assertEquals(175.75, voyage.getPrix());
        assertEquals("MXP", voyage.getAeroportDepart());
        assertEquals("Malpensa", voyage.getAeroportArrivee());
        assertEquals(120, voyage.getNbrPlaces());
    }
    
    @Test
    public void testToString() {
        Voyage voyage = new Voyage(10, "Tokyo", 550.0, "NRT", "Haneda", 200);
        String toStringOutput = voyage.toString();
        
        // Vérifier que la chaîne retournée contient certaines informations clés
        assertTrue(toStringOutput.contains("id=10"));
        assertTrue(toStringOutput.contains("destination='Tokyo'"));
        assertTrue(toStringOutput.contains("prix=550.0"));
        assertTrue(toStringOutput.contains("aeroportDepart='NRT'"));
        assertTrue(toStringOutput.contains("aeroportArrivee='Haneda'"));
        assertTrue(toStringOutput.contains("nbrPlaces=200"));
    }
    
    @Test
    public void testToArray() {
        Voyage voyage = new Voyage(3, "New York", 450.0, "JFK", "LaGuardia", 180);
        Object[] arr = voyage.toArray();
        
        assertEquals(6, arr.length, "Le tableau doit contenir 6 éléments");
        assertEquals(3, arr[0]);
        assertEquals("New York", arr[1]);
        assertEquals(450.0, arr[2]);
        assertEquals("JFK", arr[3]);
        assertEquals("LaGuardia", arr[4]);
        assertEquals(180, arr[5]);
    }
}
