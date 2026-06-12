
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_d1ff64522dbae55a409bf8508c333fb7 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_83ec22c368cc6228656c63a849b242a3 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_ledger_query", ({ ["q"] : "" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["color"] : "#4e4e6a", ["cursor"] : "pointer", ["fontSize"] : "18px", ["&:hover"] : ({ ["color"] : "#f0f0fa" }) }),onClick:on_click_83ec22c368cc6228656c63a849b242a3},children)
    )
});
