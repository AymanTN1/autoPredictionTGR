package dao;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;

public class db {
        private static final String URL = "jdbc:mysql://localhost:3306/agence_voyage";
    private static final String USER = "root";
    private static final String PASSWORD = "";
    private static Connection connection;

    private db() {}

    public static Connection getConnection() {
        if (connection == null) {
            try {
                Class.forName("com.mysql.cj.jdbc.Driver");
                connection = DriverManager.getConnection(URL, USER, PASSWORD);
            } catch (ClassNotFoundException | SQLException e) {
                e.printStackTrace();
            }
        }
        return connection;
    }

    
    

}
