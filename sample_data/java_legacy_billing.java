/**
 * LegacyBillingService.java
 *
 * PURPOSE: Legacy billing system that calculates invoices, applies
 * tiered discounts, processes payments via JDBC, and generates
 * billing reports. Written in early Java style with deprecated APIs.
 *
 * THIS IS SAMPLE DATA for testing the agent network.
 */

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.io.FileWriter;
import java.io.BufferedWriter;
import java.io.IOException;
import java.util.Date;
import java.util.Vector;
import java.util.Hashtable;

public class LegacyBillingService {

    private static final String DB_URL = "jdbc:oracle:thin:@legacy-db:1521:BILLINGDB";
    private static final String DB_USER = "billing_user";
    private static final String DB_PASS = "billing_pass123";
    private static final double TIER1_DISCOUNT = 0.05;
    private static final double TIER2_DISCOUNT = 0.10;
    private static final double TIER3_DISCOUNT = 0.15;
    private static final double TIER1_THRESHOLD = 1000.00;
    private static final double TIER2_THRESHOLD = 5000.00;
    private static final double TIER3_THRESHOLD = 10000.00;
    private static final double TAX_RATE = 0.08;
    private static final String REPORT_PATH = "C:\\billing\\reports\\monthly_report.txt";

    private Connection dbConnection;
    private Vector invoiceList;
    private Hashtable customerCache;

    public LegacyBillingService() {
        this.invoiceList = new Vector();
        this.customerCache = new Hashtable();
    }

    @Deprecated
    public void initializeConnection() throws SQLException {
        try {
            Class.forName("oracle.jdbc.driver.OracleDriver");
        } catch (ClassNotFoundException e) {
            System.out.println("Oracle JDBC Driver not found!");
            return;
        }
        dbConnection = DriverManager.getConnection(DB_URL, DB_USER, DB_PASS);
    }

    public double calculateInvoiceTotal(String customerId, double subtotal) {
        double discount = calculateTieredDiscount(subtotal);
        double discountedAmount = subtotal - discount;
        double tax = discountedAmount * TAX_RATE;
        double total = discountedAmount + tax;

        if (isPreferredCustomer(customerId)) {
            total = total * 0.95;
        }

        return total;
    }

    private double calculateTieredDiscount(double amount) {
        if (amount >= TIER3_THRESHOLD) {
            return amount * TIER3_DISCOUNT;
        } else if (amount >= TIER2_THRESHOLD) {
            return amount * TIER2_DISCOUNT;
        } else if (amount >= TIER1_THRESHOLD) {
            return amount * TIER1_DISCOUNT;
        }
        return 0.0;
    }

    private boolean isPreferredCustomer(String customerId) {
        String sql = "SELECT preferred_status FROM customers WHERE customer_id = '" + customerId + "'";
        try {
            PreparedStatement stmt = dbConnection.prepareStatement(sql);
            ResultSet rs = stmt.executeQuery();
            if (rs.next()) {
                return "Y".equals(rs.getString("preferred_status"));
            }
        } catch (SQLException e) {
            System.out.println("Error checking customer status: " + e.getMessage());
        }
        return false;
    }

    @SuppressWarnings("deprecation")
    public void processMonthlyBilling() throws SQLException {
        String sql = "SELECT customer_id, SUM(amount) as total FROM orders " +
                     "WHERE billing_date >= ? AND billing_date < ? GROUP BY customer_id";
        PreparedStatement stmt = dbConnection.prepareStatement(sql);

        Date today = new Date();
        Date firstOfMonth = new Date(today.getYear(), today.getMonth(), 1);

        stmt.setDate(1, new java.sql.Date(firstOfMonth.getTime()));
        stmt.setDate(2, new java.sql.Date(today.getTime()));

        ResultSet rs = stmt.executeQuery();
        while (rs.next()) {
            String custId = rs.getString("customer_id");
            double total = rs.getDouble("total");
            double invoiceTotal = calculateInvoiceTotal(custId, total);
            insertInvoice(custId, invoiceTotal);
            invoiceList.addElement(custId + ":" + invoiceTotal);
        }
    }

    private void insertInvoice(String customerId, double amount) throws SQLException {
        String sql = "INSERT INTO invoices (customer_id, amount, created_date, status) " +
                     "VALUES (?, ?, SYSDATE, 'PENDING')";
        PreparedStatement stmt = dbConnection.prepareStatement(sql);
        stmt.setString(1, customerId);
        stmt.setDouble(2, amount);
        stmt.executeUpdate();
    }

    public void generateBillingReport() {
        try {
            BufferedWriter writer = new BufferedWriter(new FileWriter(REPORT_PATH));
            writer.write("MONTHLY BILLING REPORT");
            writer.newLine();
            writer.write("Generated: " + new Date().toString());
            writer.newLine();
            writer.write("================================");
            writer.newLine();

            for (int i = 0; i < invoiceList.size(); i++) {
                writer.write(invoiceList.elementAt(i).toString());
                writer.newLine();
            }

            writer.close();
        } catch (IOException e) {
            System.out.println("Error writing report: " + e.getMessage());
        }
    }

    public void closeConnection() {
        try {
            if (dbConnection != null && !dbConnection.isClosed()) {
                dbConnection.close();
            }
        } catch (SQLException e) {
            System.out.println("Error closing connection: " + e.getMessage());
        }
    }
}
