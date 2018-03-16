# Endpoints
`/expenses_api/<api version>`
## v1
> All endpoints expect a `x-firebase-auth` header with the firebase [auth token](https://firebase.google.com/docs/auth/admin/create-custom-tokens) as a value.

* **GET** `/get_expenses_list?start_from_id=<string>&start_from_property=<name of a property of an expense>&start_from_property_value=<any>&batch_size=<int>&ordering_direction=<asc|desc>`
  Gets a list of expenses from newer-to-older order.
  *  URL args
     * `start_from_property` - the name of the property that will be used to order the results. Currently only `timestamp_utc` is supported.
     * `?start_from_property_value` - the value of the above property. The search will start from the expense with this value for the `start_from_property` (exclusive). Can be empty, in which can the search will start from the newest expenses
     * `start_from_id` - mandatory if `start_from_property_value` is set; the `id` property of the expense
     * `?batch_size` - the __maximum__ size of the response. Optional. Default 10
     * `ordering_direction` - either "asc" or "desc"

  * `200` on successfull response
    ```
    [ {<Expense Object>}* ]
    ```
  * `400` on malformed request
    ```{error: "<reason>"}```
  * `413` if the `batch_size` is too large
   ```{error: "<ApiError.BATCH_SIZE_EXCEEDED>"}```
* __POST__ `/persist`
  * payload: `{<Expense Object with id=null>}`
  * 200 on expense persisted
  `{<Expense object>}`
  * 400 on expense not processable
  `{error: "<reason>"}`
* __PUT__ `/update`
  * payload
      ```
      {
        "updated": <Expense object>,
        "previous_state": <Expense object>
      }
      ```
  * response
      * `200` on expense updated
        `{<Expense object>}`
      * `400` on expense not processible (invalid expense)
      `{error: "<reason>"}`
      * `404` on expense with such id not found or not authorized to update this expense
      `{error: "<reason>"}`
* __POST__ `/remove`
  * payload
     ```
     {<expense object>}
     ```
  * response
    * `200` on successful deletion
    * `404` if no such expense / not authorized to delete this expense
  `{msg: "<reason>"}`
* __POST__ `/sync`
    Given a set of expense-representations from the client, get which of these expenses should be removed, updated or if additional expenses should be added to the client, so that the client's data is consistent with the backend's.
    Semantically it is a GET as it doesn't change anything on the "server". Using POST because it allows for a request     body.
    * payload
      ```

         {
           "<expense.id>" : {
                        "timestamp_utc":"<ts>",
                        "timestamp_utc_updated":"<ts>"
            },*
         }

       ```
    * response
      * `200`
        ```
            {
              "to_add": [<Expense object>],
              "to_remove": [<id>],
              "s": [<Expense object>]
            }
        ```
      * `400` on invalid request
      ```{"error": "<error msg>"}```
      * `413` if at the moment the server cannot retrieve all of the persisted items of the user and thus cannot process the sync.


* __GET__ /statistics/<from_dt_utc:ts>/<to_dt_utc:ts>
    Returns an object containing the sum of all expenses, grouped by currency. If no expenses in the given time window
    an empty object will be returned.
    The time-span of the requested window must be less than two months (60 days).
    * url params:
      * `from_dt_utc` - start (inclusive) searching from this datetime. iso8601
      * `to_dt_utc` - search until then (__exclusive__). iso8601

    * response
      * `200`
        ```
        {
            "<3-letter-currency-code>" : <number>,
            ...
        }
        ```
      * `400` - if the requested time-span is more than two months