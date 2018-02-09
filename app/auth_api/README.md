# Auth API
`/auth_api`
* __POST__ `/register_new` - adds a user to our system so that we begin to accept other requests from him.
  * payload:
    ```
    {
    }
    ```
  * responses
    *  `200` on successfull
    *  `400` if there's already an existing customer with the same `uid`
    *  `403` if the auth token doesn't correspond to a valid uid
*  __DELETE__ `/delete_user` - deletes the user and __all__ of its associated data
   * payload
      the auth token from the custom auth header is used
   * responses
     *  `200` on successful deletion
     *  `403` if the user that sent the request is not authorized
     *  `404` if no such user