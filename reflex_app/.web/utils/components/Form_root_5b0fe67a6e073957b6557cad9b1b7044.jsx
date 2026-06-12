
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,getRefValue,getRefValues,isTrue} from "$/utils/state"
import {Root as RadixFormRoot} from "@radix-ui/react-form"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Form_root_5b0fe67a6e073957b6557cad9b1b7044 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);

    const handleSubmit_3fc41e13fa0db32e8d9d04ce60a5e62b = useCallback((ev) => {
        const $form = ev.target
        ev.preventDefault()
        const form_data = {...Object.fromEntries(new FormData($form).entries()), ...({  })};

        (((...args) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.login", ({ ["form_data"] : form_data }), ({  })))], args, ({  }))))(ev));

        if (false) {
            $form.reset()
        }
    })
    


    return(
        jsx(RadixFormRoot,{className:"Root ",css:({ ["width"] : "100%" }),onSubmit:handleSubmit_3fc41e13fa0db32e8d9d04ce60a5e62b},children)
    )
});
