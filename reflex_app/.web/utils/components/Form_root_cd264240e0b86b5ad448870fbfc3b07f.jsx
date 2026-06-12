
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,getRefValue,getRefValues,isTrue} from "$/utils/state"
import {Root as RadixFormRoot} from "@radix-ui/react-form"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Form_root_cd264240e0b86b5ad448870fbfc3b07f = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);

    const handleSubmit_c836bfd47002e2d6fe38babee06cc1ef = useCallback((ev) => {
        const $form = ev.target
        ev.preventDefault()
        const form_data = {...Object.fromEntries(new FormData($form).entries()), ...({  })};

        (((...args) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.signup", ({ ["form_data"] : form_data }), ({  })))], args, ({  }))))(ev));

        if (false) {
            $form.reset()
        }
    })
    


    return(
        jsx(RadixFormRoot,{className:"Root ",css:({ ["width"] : "100%" }),onSubmit:handleSubmit_c836bfd47002e2d6fe38babee06cc1ef},children)
    )
});
