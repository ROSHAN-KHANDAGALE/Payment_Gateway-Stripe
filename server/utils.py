from rest_framework import status
from rest_framework.response import Response

def success_response(message, data=None, status_code=status.HTTP_200_OK, api_status_code=status.HTTP_200_OK):
    """
    A utility function to generate success API responses.

    Args:
    - message (str): A message to send with the response.
    - data (dict, optional): The data to include in the response. Defaults to None.
    - status_code (int, optional): The HTTP status code for the response. Defaults to HTTP_200_OK.

    Returns:
    - Response: A DRF Response object with the provided message, data, and status code.
    """
    response_data = {
        "message": message,
        "data": data if data else {},
        "status": status_code,
    }

    return Response(response_data, status=api_status_code, )


def error_response(message, errors=None, status_code=status.HTTP_400_BAD_REQUEST, api_status_code=status.HTTP_400_BAD_REQUEST):
    """
    A utility function to generate error API responses.

    Args:
    - message (str): A message to send with the response.
    - errors (dict, optional): The error details to include in the response. Defaults to None.
    - status_code (int, optional): The HTTP status code for the response. Defaults to HTTP_400_BAD_REQUEST.

    Returns:
    - Response: A DRF Response object with the provided message, error details, and status code.
    """
    response_data = {
        "message": message,
        "errors": errors if errors else {},
        "status": status_code,
    }

    return Response(response_data, status=api_status_code)