
import {Fragment,memo,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_f809b5145f7f579d16111186de27c4ae = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);

                useEffect(() => {
                    ((...args) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.on_dashboard_load", ({  }), ({  })))], args, ({  }))))()
                    return () => {
                        
                    }
                }, []);



    return(
        jsx(RadixThemesBox,{css:({ ["background"] : "#0C0C10", ["color"] : "#FFFFFF", ["fontFamily"] : "'Inter', system-ui, sans-serif", ["--default-font-family"] : "'Inter', system-ui, sans-serif", ["minHeight"] : "100vh" })},children)
    )
});
