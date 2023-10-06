# Flea Market
#### Video Demo: https://youtu.be/Ft6wMBcDLKk

## Description:
Flea Market is a simulation of an online platform which facilitates users to do shopping and to sell their products. In Flea Market users can access the  "Shopping" and "My Store" portals. In the "Shopping" portal, users can select their desired product andsimply checkout. Flea Market will then deliver the order to the buyers'registered address. The "My Store" portal is the users' own retail store. Users can register their own products there for selling. Registered products will be displayed in the product browser in the "Shopping" portal. Once orders are received, sellers can order for delivery and then Flea Market will collect the product from sellers for delivery. 
### Site configuration
All pages in this web site use the same layout template, which consists of a top navigation bar, laft and right side bars, main content and footer. Before logging in, there are links to login or register page for selection in the top navigation bar. After selecting, the corresponding content will be displayed. After login, the main features of the site will be displayed.

At the top navigation bar, right next to the site logo users can see all the links to different pages in the site. At the right side of the nav bar, users is greeted with a welcome message. The welcome message is actually a dropdown list with options for users to update their information or log out.

The design of Flea Market site consists of 2 portals: "Shopping" and "Selling". A button is provided at top navigation bar for users to switch between the two portals. Each portal consist of different pages, a session parameter "portal" is used to select the corresponding links to be displayed in the top navigation bar.

Left nav bar is used for navigation or options selecion within the page. Right nav bar is used for display of additional information or error message.
Main content area is the only area that expect content overflow, and thus it is scrollable.

Footer is used to display credit.
### User account

#### Register
When users visit the Flea Market site the first time, they will be directed to the login page. If users can proceed to the register page to create a new account if they do not have one yet. To create a new account, users have to input a username, which is not already existing in this platform, password and password confirmation. Users also have to input contact number andaddress for delivery purpose. Submission will be rejected if the username is already existing or password confirmation does not match with password.

#### Login / Logout
After creating their own account, users have to input the correct username and password to login in the login page. If users have successfully logged in, users will see a dropdown button with welcome message on the right side of the top navigation bar. In the dropdown list, users can choose to proceed to the "Setting" page where they can update their personal information or log out.

#### Setting
Users can update their latest contact no and address in this page. Users can also change their password here. Users will have to input the correct current password and new password together with new password confirmation to submit the password change request. Change password request will be rejected if the current password is not correct or new password confirmation does not match with new password. Users can delete their accout when it is no longer required. Once delete request is confirmed, the account will be deactivated and cannot be logged in again.

### "Shopping" Portal
In Shopping portal, users have access to the "Browser", "My Cart" and "My Wallet" page from the navigation bar.Users can:

    - make cash deposit and withdrawal,
    - browser products,
    - put products into their shopping cart,
    - check-out their cart, and
    - access order status and transaction records. 
  

#### Browser
All available products are displayed on this page by default. Products can be filtered by categories shows on the left navigation bar. Categories are preset by the platform designer as a global set and it defines the category options at browser filtering and product detials setting.

In each product card, product name and selling price are displayed as well as an "Add to cart" button. The “Add to Cart” button is provided for adding the product into the buyer’s shopping cart. Selected items will be displayed in the "My Cart" page.

#### My Cart
In "My Cart" page all the products that have been selected will be displayed. Users can adjust the quantity by the "+1"/"-1" button or directly select in the dropdown list. Users can also remove the item if they change their mind. The total cost of the cart, buyer's contact and delivery address are displayed at the top of the page. User can check out the cart by clicking the "Check out" button. Once the cart is checked out, a new order is created and the cart will be emptied. The new order will be displayed in the "My Wallet" page. Checking out will be unsuccessful if user has not enough balance or product stock is less then required quantity.

#### My Wallet
In "My Wallet" page users can select on the left navigation bar either

    "My Orders" which lists out all the orders the user made. The order list is expandable to display the details of each order. Order status will be updated according to the delivery status of the item.  

or

    "Balance and transactions" where users can deposit and withdraw the wallet balance and access all the transactions record of the wallet in this account.

### "Selling" Portal
In "Selling" portal, users have access to the "Dashboard", "My Store" and "Orders& Delivery" page from the navigation bar. Users can:

    - transfer cash balance between "My Store" and "My Wallet",
    - register their products for selling,
    - receive orders and arrange delivery,
    - review sale performance trends of each product, and
    - access order and transaction records.


#### Dashboard
On the "Dashboard" page, users can review the sales performance in the past 6 months of each of their registered products which is currently active. Users can select to display either the sale volume or the sale revenue trends and they are displayed in the form of a bar chart.

#### My Store
In "My Store" page users can select on the left navigation bar either

    "My Inventories" where users can register their products in this page by clicking the "Create New Product" button at the bottom of the page and input all product details in the pop-up form. Once a product is registered, its name, category, price and stock will be displayed. Product image will be displayed in the "Browser" page.

    Users can revise any product details or increase stock for each product with the pop-up form called by the "Revise" button. Users can also delete the item if it is no longer available with the "Delete" button.

or

    "Balance & Transactions" where users can transfer balance between the store and the wallet and access all the transactions record of the store in this account.

#### Orders & Delivery
In the "Orders & Delivery" page, users can see all the orders received. User will have to arrange the delivery in order to fulfill the orders. To arrange a delivery, users have to select the items that are ready to be collected with the checkbox on the right side of the orders table and click "Deliver!" button at top-right corner of the table. A delivery charge will be deducted from store balance automatically once delivery request is made.

Delivery request will be rejected if the store balance is less then the total delivery cost. Once a new delivery order is successfully made, it will be displayed in the Delivery Orders table. Delivery charges will be logged in the transaction table. Item status will change from "Pending" to "Delivered". Once all items in an order is delivered, the order status will change from "Pending" to "Delivered".
