from typing import Annotated
from typing_extensions import TypedDict


class State(TypedDict):
    # -- SEARCH TOPIC INDEX -- ##
    search_topic_index : Annotated[bool, "read the search_topic_index.md that match or not match the search topic."]

    # -- Read user_profiles.md file -- ##
    read_user_profiles : Annotated[bool, "read the user_profiles.md file that match or not match the search topic."]

    # -- Create user_profiles.md files if does not exist -- ##
    create_user_profiles : Annotated[bool, "A flag indicating whether to create user_profiles.md or not."]

    # -- MATCH OR NOT MATCH THE SEARCH TOPIC -- ##
    read_specific_topic : Annotated[str, "read the specific_topic.md file."] # if match 
    read_no_specific_topic : Annotated[str, "returnt the empty string if the specific_topic.md and not found."] # no match 

    # -- Assemble the context -- ##
    assemble_context : Annotated[str, "merge the context from vary context base on user"]

    # -- Generate the final response -- ##
    generate_final_response : Annotated[str, "prepare for generate the final response based on the context and user input."]

    # -- Action output -- ##
    action_output : Annotated[str, "the final output that will be return to the user"]

    # -- Decision is it worth to recognize (Agent Memory)-- ##
    is_recognize : Annotated[bool, "A flag indicating whether to recognize the user input or not."]

    # -- IF YEST (1) -- #

    ## -- if Exist topic -- ##
    update_topic_md : Annotated[bool, "A flag indicating whether to update the desired .md file or not."] # return 1 #
    content_updated_topic_md : Annotated[str, "the content that will be updated to desired .md file."]

    ## -- if new topic -- ##
    create_new_topic_md : Annotated[bool, "A flag indicating whether to create a new topic.md file or not."] # return 1 #
    content_new_topic_md : Annotated[str, "the content for the new topic.md file."]
